# llama.cpp OpenAI-Compatible Test Endpoint

This companion note describes a small local model endpoint for testing CodeGopher's initial OpenAI-compatible provider path.

## Target VM

- 2 CPU cores
- 4 GB RAM
- `llama.cpp` already compiled

Use a small quant and modest context size so the process stays inside the VM's memory budget.

## Start Server

From the compiled `llama.cpp` directory:

```bash
./llama-server \
  -hf unsloth/Qwen3.5-2B-GGUF:Q4_K_M \
  --alias qwen3.5-2b \
  --host 0.0.0.0 \
  --port 8000 \
  --ctx-size 2048 \
  --threads 2 \
  --batch-size 128 \
  --ubatch-size 32
```

The OpenAI-compatible base URL is:

```text
LOCAL_OPENAI_COMPATIBLE_ENDPOINT
```

Use any placeholder API key if the client requires one, such as:

```text
sk-local-test
```

## Smoke Test

Run this from the VM:

```bash
curl $LOCAL_OPENAI_COMPATIBLE_ENDPOINT/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-local-test" \
  -d '{
    "model": "qwen3.5-2b",
    "messages": [{"role": "user", "content": "Say hello in one sentence."}],
    "temperature": 0.2,
    "max_tokens": 64
  }'
```

If the VM starts swapping or the process is killed, reduce `--ctx-size 2048` to `1024` or use a smaller quant such as `Q3_K_M`.
