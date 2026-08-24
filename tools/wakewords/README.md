# Bundled wake-word models

`hey_synapse.onnx` / `hey_synapse.tflite` — the on-device "Hey Synapse" hotword
model. This is the default detector for the wake word feature (see
`website/docs/user-guide/features/wake-word.md`); no training or setup is
required to say "hey synapse".

- **Engine:** [openWakeWord](https://github.com/dscripka/openWakeWord) (Apache-2.0).
- **Provenance:** trained with the openWakeWord training pipeline (synthetic
  TTS-generated speech), which produces both the `.onnx` and `.tflite` artifacts.
  Redistribution is permitted under the openWakeWord license.
- **Label:** the model registers as `hey_synapse` (matches the filename).
- **Runtime:** openWakeWord's shared feature-extraction models (melspectrogram +
  embedding) are NOT bundled here — they are fetched once on first use by
  `tools/wake_word.py` via `openwakeword.utils.download_models()`.

To use a different phrase, train your own model and point
`wake_word.openwakeword.model` at its path, or set a built-in openWakeWord name
(`hey_jarvis`, `alexa`, `hey_mycroft`, …). See the wake-word docs for the
training guide.
