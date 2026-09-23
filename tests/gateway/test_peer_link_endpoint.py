"""Tests for Peer Link per-instance endpoint addresses.

The two properties that matter:

  * **unique per instance** — two instances never collide, and a label is
    stable across restarts (minted once, persisted);
  * **unguessable** — the label carries no information derived from the public
    peer id, so knowing a public key does not reveal the address.

Also covered: the TLS wildcard-depth caveat, which is the difference between
"works for free" and "fails certificate validation" for a deep base domain.

Every test writes only under ``tmp_path``.
"""

from __future__ import annotations

import json
import os
import stat

import pytest

from gateway.peer_link.endpoint import (
    DEFAULT_BASE_DOMAIN,
    LABEL_ALPHABET,
    LABEL_LENGTH,
    EndpointRegistry,
    certificate_note,
    generate_label,
    hostname_for,
    public_address,
    validate_address_mode,
    validate_domain,
    validate_label,
)


class TestGenerateLabel:
    def test_length_and_alphabet(self):
        label = generate_label()
        assert len(label) == LABEL_LENGTH
        assert all(c in LABEL_ALPHABET for c in label)

    def test_labels_are_unique(self):
        labels = {generate_label() for _ in range(500)}
        assert len(labels) == 500  # no collision in 500 draws

    def test_excludes_confusable_characters(self):
        """No 0/O/1/l — these are misread when a human copies an address."""
        assert not set("0o1l") & set(LABEL_ALPHABET)

    def test_entropy_is_ample(self):
        import math

        bits = LABEL_LENGTH * math.log2(len(LABEL_ALPHABET))
        assert bits > 128  # far beyond enumeration

    def test_rejects_too_short(self):
        with pytest.raises(ValueError):
            generate_label(4)

    def test_rejects_over_dns_limit(self):
        with pytest.raises(ValueError):
            generate_label(64)


class TestValidateLabel:
    def test_accepts_generated(self):
        assert validate_label(generate_label()) is True

    @pytest.mark.parametrize(
        "bad",
        [
            "",
            ".",
            "a.b",            # a dot would escape the label position
            "../etc",         # path traversal shape
            "a/b",
            "*",
            "UPPER",
            "has space",
            "-leading",
            "trailing-",
            "x" * 64,
        ],
    )
    def test_rejects_unsafe(self, bad):
        assert validate_label(bad) is False

    def test_rejects_non_string(self):
        assert validate_label(None) is False
        assert validate_label(123) is False


class TestValidateDomain:
    def test_accepts_real_domains(self):
        for good in ["example.com", "synz.zone.id", "a-b.example.co.uk"]:
            assert validate_domain(good) is True

    @pytest.mark.parametrize(
        "bad",
        ["", "a b", "a/b", "*.evil.com", "a..b", ".leading", "trailing.",
         "UPPER.com", "a_b.com", None, 123],
    )
    def test_rejects_unsafe(self, bad):
        assert validate_domain(bad) is False


class TestHostnameFor:
    def test_composes(self):
        assert hostname_for("abc", "synz.zone.id") == "abc.synz.zone.id"

    def test_refuses_unsafe_label(self):
        with pytest.raises(ValueError):
            hostname_for("a.b", "synz.zone.id")

    def test_refuses_unsafe_domain(self):
        for bad in ["", "has space", "a/b", "*.evil.com"]:
            with pytest.raises(ValueError):
                hostname_for("abc", bad)

    def test_normalises_domain(self):
        assert hostname_for("abc", ".SYNZ.Zone.ID.") == "abc.synz.zone.id"


class TestCertificateNote:
    """The rule is apex-relative depth, NOT a label count.

    This distinction was got wrong once: ``aikernel.qzz.io`` and
    ``synz.zone.id`` both have three labels, but the first is a zone apex
    (covered by its own free wildcard) while the second is a hostname inside
    ``zone.id`` (not covered). Counting labels cannot tell them apart.
    """

    def test_apex_is_covered(self):
        note = certificate_note("example.com", "example.com")
        assert "covers" in note
        assert "No paid certificate" in note

    def test_three_label_apex_is_covered(self):
        """A 3-label name that IS the zone apex still works — the case a
        label-count heuristic got wrong."""
        note = certificate_note("aikernel.qzz.io", "aikernel.qzz.io")
        assert "No paid certificate" in note
        assert "will NOT cover" not in note

    def test_hostname_inside_foreign_zone_warns(self):
        """The real failing case: base is one label below the apex."""
        note = certificate_note("synz.zone.id", "zone.id")
        assert "will NOT cover" in note
        assert "1 label(s) below" in note

    def test_unknown_apex_asks_instead_of_guessing(self):
        """Without the apex we cannot know — so we must not claim either way."""
        note = certificate_note("synz.zone.id")
        assert "dig +short NS" in note
        assert "will NOT cover" not in note
        assert "No paid certificate" not in note

    def test_rejects_invalid_domain(self):
        assert "not a valid DNS name" in certificate_note("a b")


class TestEndpointRegistry:
    def test_mints_once_and_is_stable(self, tmp_path):
        reg = EndpointRegistry(tmp_path)
        first = reg.own_hostname()
        second = reg.own_hostname()
        assert first is not None and second is not None
        assert first == second
        assert first.endswith("." + DEFAULT_BASE_DOMAIN)

    def test_distinct_instances_never_collide(self, tmp_path):
        hosts = {
            EndpointRegistry(tmp_path / f"i{i}").own_hostname() for i in range(50)
        }
        assert len(hosts) == 50

    def test_peek_does_not_create(self, tmp_path):
        reg = EndpointRegistry(tmp_path)
        assert reg.own_hostname(create=False) is None
        # ...and nothing was written as a side effect.
        assert not (tmp_path / "endpoints.json").exists()

    def test_rotate_changes_address(self, tmp_path):
        reg = EndpointRegistry(tmp_path)
        old = reg.own_hostname()
        assert old is not None
        new = reg.rotate()
        assert new != old
        assert reg.own_hostname() == new  # rotation persisted

    def test_unguessable_from_peer_id(self, tmp_path):
        """The label must not be derivable from a public peer id."""
        from gateway.peer_link.identity import PeerIdentity

        ident = PeerIdentity.generate()
        reg = EndpointRegistry(tmp_path)
        hostname = reg.own_hostname()
        assert hostname is not None
        label = hostname.split(".")[0]
        # A peer id is public; the label must share nothing with it.
        assert label not in ident.peer_id
        assert ident.peer_id[:10] not in hostname

    def test_file_is_owner_only(self, tmp_path):
        reg = EndpointRegistry(tmp_path)
        reg.own_hostname()
        path = tmp_path / "endpoints.json"
        mode = stat.S_IMODE(os.stat(path).st_mode)
        assert mode == 0o600

    def test_corrupt_file_recovers(self, tmp_path):
        (tmp_path / "endpoints.json").write_text("{not json", encoding="utf-8")
        reg = EndpointRegistry(tmp_path)
        assert reg.own_hostname()  # mints fresh rather than raising

    def test_corrupt_label_is_replaced(self, tmp_path):
        """A tampered label must not be trusted into a hostname."""
        (tmp_path / "endpoints.json").write_text(
            json.dumps({"self": {"label": "../../evil"}, "peers": {}}),
            encoding="utf-8",
        )
        reg = EndpointRegistry(tmp_path)
        hostname = reg.own_hostname()
        assert hostname is not None
        assert ".." not in hostname
        assert "evil" not in hostname

    def test_base_domain_from_config(self, tmp_path):
        reg = EndpointRegistry(tmp_path, "mydomain.net")
        hostname = reg.own_hostname()
        assert hostname is not None
        assert hostname.endswith(".mydomain.net")
        assert reg.base_domain == "mydomain.net"


class TestPublicAddress:
    """``path`` mode exists because the base domain may not be an apex we own.

    ``synz.zone.id`` is a hostname inside the ``zone.id`` zone, so
    ``<label>.synz.zone.id`` is too deep for a free one-level wildcard. Sharing
    one hostname and telling peers apart by path needs only an ordinary cert.
    """

    def test_subdomain_mode_is_bare_hostname(self):
        assert public_address("abc", "example.com", "subdomain") == "abc.example.com"

    def test_path_mode_is_hostname_plus_path(self):
        assert public_address("abc", "synz.zone.id", "path") == "synz.zone.id/peer/abc"

    def test_default_mode_is_subdomain(self):
        assert public_address("abc", "example.com") == "abc.example.com"

    def test_path_mode_rejects_unsafe_label(self):
        """A label that could escape the path must not compose at all."""
        for bad in ["../evil", "a/b", "a.b", "*", "UPPER", ""]:
            with pytest.raises(ValueError):
                public_address(bad, "synz.zone.id", "path")

    def test_path_mode_rejects_unsafe_domain(self):
        for bad in ["", "a/b", "*.evil.com", "has space"]:
            with pytest.raises(ValueError):
                public_address("abc", bad, "path")

    def test_rejects_unknown_mode(self):
        for bad in ["", "hostname", "PATH", None, 123]:
            with pytest.raises(ValueError):
                public_address("abc", "example.com", bad)


class TestValidateAddressMode:
    def test_accepts_known_modes(self):
        assert validate_address_mode("subdomain") is True
        assert validate_address_mode("path") is True

    @pytest.mark.parametrize("bad", ["", "Path", "dns", None, 1, ["path"]])
    def test_rejects_unknown(self, bad):
        assert validate_address_mode(bad) is False


class TestCertificateNotePathMode:
    def test_path_mode_says_one_cert_covers_all(self):
        note = certificate_note("synz.zone.id", "zone.id", "path")
        assert "single hostname" in note
        assert "no wildcard" in note
        assert "will NOT cover" not in note

    def test_path_mode_ignores_apex_question(self):
        """Even without knowing the apex, path mode is a definite answer."""
        note = certificate_note("synz.zone.id", None, "path")
        assert "single hostname" in note
        assert "dig +short NS" not in note

    def test_subdomain_verdict_offers_path_escape(self):
        """The failing case must point at the fix, not just the problem."""
        note = certificate_note("synz.zone.id", "zone.id", "subdomain")
        assert "will NOT cover" in note
        assert "address_mode: path" in note

    def test_unknown_mode_is_reported(self):
        assert "not a known addressing mode" in certificate_note(
            "example.com", "example.com", "bogus"
        )


class TestEndpointRegistryPathMode:
    def test_path_mode_address_shape(self, tmp_path):
        reg = EndpointRegistry(tmp_path, "synz.zone.id", "path")
        address = reg.own_address()
        assert address is not None
        assert address.startswith("synz.zone.id/peer/")
        assert reg.mode == "path"

    def test_own_hostname_still_bare_in_path_mode(self, tmp_path):
        """In path mode every peer shares the base domain as the hostname."""
        reg = EndpointRegistry(tmp_path, "synz.zone.id", "path")
        hostname = reg.own_hostname()
        assert hostname == "synz.zone.id"
        assert "/" not in hostname

    def test_address_stable_across_calls(self, tmp_path):
        reg = EndpointRegistry(tmp_path, "synz.zone.id", "path")
        assert reg.own_address() == reg.own_address()

    def test_rotate_returns_full_address(self, tmp_path):
        reg = EndpointRegistry(tmp_path, "synz.zone.id", "path")
        old = reg.own_address()
        new = reg.rotate()
        assert new != old
        assert new.startswith("synz.zone.id/peer/")
        assert reg.own_address() == new

    def test_mode_persisted_in_file(self, tmp_path):
        EndpointRegistry(tmp_path, "synz.zone.id", "path").own_address()
        raw = json.loads((tmp_path / "endpoints.json").read_text(encoding="utf-8"))
        assert raw["self"]["mode"] == "path"

    def test_rejects_unknown_mode(self, tmp_path):
        with pytest.raises(ValueError):
            EndpointRegistry(tmp_path, "synz.zone.id", "bogus")

    def test_path_mode_peek_does_not_create(self, tmp_path):
        reg = EndpointRegistry(tmp_path, "synz.zone.id", "path")
        assert reg.own_address(create=False) is None
        assert not (tmp_path / "endpoints.json").exists()


class TestRememberAddress:
    def test_remembers_subdomain_shape(self, tmp_path):
        reg = EndpointRegistry(tmp_path)
        reg.remember_address("pl1a", "xyz.example.com")
        assert reg.lookup("pl1a") == "xyz.example.com"

    def test_remembers_path_shape(self, tmp_path):
        reg = EndpointRegistry(tmp_path)
        reg.remember_address("pl1a", "synz.zone.id/peer/abc")
        assert reg.lookup("pl1a") == "synz.zone.id/peer/abc"

    def test_normalises_case_and_space(self, tmp_path):
        reg = EndpointRegistry(tmp_path)
        reg.remember_address("pl1a", "  Synz.Zone.ID/peer/ABC  ")
        assert reg.lookup("pl1a") == "synz.zone.id/peer/abc"

    @pytest.mark.parametrize(
        "bad",
        [
            "a.b/c",
            "synz.zone.id/other/abc",   # wrong prefix
            "synz.zone.id/peer/../etc",  # traversal in the path
            "synz.zone.id/peer/",        # empty label
            "synz.zone.id/peer/a.b",     # dot escapes the path segment
            "..",
            "*",
            "a b",
            "",
        ],
    )
    def test_rejects_unsafe(self, tmp_path, bad):
        reg = EndpointRegistry(tmp_path)
        with pytest.raises(ValueError):
            reg.remember_address("pl1a", bad)

    def test_requires_peer_id(self, tmp_path):
        reg = EndpointRegistry(tmp_path)
        with pytest.raises(ValueError):
            reg.remember_address("", "xyz.example.com")


class TestPeerEndpoints:
    def test_remember_and_lookup(self, tmp_path):
        reg = EndpointRegistry(tmp_path)
        reg.remember("pl1abc", "xyz.synz.zone.id")
        assert reg.lookup("pl1abc") == "xyz.synz.zone.id"

    def test_forget(self, tmp_path):
        reg = EndpointRegistry(tmp_path)
        reg.remember("pl1abc", "xyz.synz.zone.id")
        assert reg.forget("pl1abc") is True
        assert reg.lookup("pl1abc") is None

    def test_rejects_unsafe_hostname(self, tmp_path):
        reg = EndpointRegistry(tmp_path)
        for bad in ["a.b/c", "..", "evil.com/../x", "*", "a b"]:
            with pytest.raises(ValueError):
                reg.remember("pl1abc", bad)

    def test_requires_peer_id(self, tmp_path):
        reg = EndpointRegistry(tmp_path)
        with pytest.raises(ValueError):
            reg.remember("", "xyz.synz.zone.id")

    def test_peers_snapshot(self, tmp_path):
        reg = EndpointRegistry(tmp_path)
        reg.remember("pl1a", "a.synz.zone.id")
        reg.remember("pl1b", "b.synz.zone.id")
        assert reg.peers() == {"pl1a": "a.synz.zone.id", "pl1b": "b.synz.zone.id"}
