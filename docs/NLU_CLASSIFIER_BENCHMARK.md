# NLU Classifier Benchmark

**Model:** `structure`
**Device:** `cpu`
**Date:** 2026-09-03T09:30:11
**Average latency:** None ms
**Reason:** No classifier met intent_accuracy >= 0.5 (best measured 17%). Using structural NLU until a competent classifier wins.

| Model | Device | Warm ms | Accuracy | JSON | Score |
|-------|--------|---------|----------|------|-------|
| coder-stable:latest | cpu | 18394.7 | 0.0 | 0.833 | 18778.1 |
| coder-stable:latest | nvidia | 1810.9 | 0.0 | 0.667 | 2327.6 |
| deepseek-coder-v2:16b | cpu | 3659.5 | 0.0 | 0.833 | 4042.8 |
| deepseek-coder-v2:16b | nvidia | 422.7 | 0.0 | 0.833 | 856.1 |
| deepseek-coder-v2:latest | cpu | 4978.0 | 0.0 | 0.833 | 5361.4 |
| deepseek-coder-v2:latest | nvidia | 444.7 | 0.0 | 0.833 | 878.0 |
| deepseek-coder:latest | cpu | 4182.9 | 0.0 | 0.833 | 4566.2 |
| deepseek-coder:latest | nvidia | 437.1 | 0.0 | 0.833 | 870.5 |
| deepseek-r1:14b | cpu | 4550.4 | 0.0 | 0.833 | 4933.7 |
| deepseek-r1:14b | nvidia | 444.5 | 0.0 | 0.833 | 877.8 |
| deepseek-r1:7b | cpu | 4258.1 | 0.0 | 0.833 | 4641.4 |
| deepseek-r1:7b | nvidia | 477.3 | 0.0 | 0.833 | 910.7 |
| devstral:latest | cpu | 4511.9 | 0.0 | 0.833 | 4895.2 |
| devstral:latest | nvidia | 727.9 | 0.0 | 0.833 | 1161.3 |
| dolphin-mistral:latest | cpu | 16819.6 | 0.0 | 0.833 | 17202.9 |
| dolphin-mistral:latest | nvidia | 658.9 | 0.0 | 0.833 | 1092.3 |
| dolphin3:latest | cpu | 14275.2 | 0.0 | 0.833 | 14658.5 |
| dolphin3:latest | nvidia | 474.6 | 0.0 | 0.833 | 907.9 |
| gemma3:12b | cpu | 4496.8 | 0.0 | 0.833 | 4880.1 |
| gemma3:12b | nvidia | 411.2 | 0.167 | 1.0 | 711.2 |
| gemma3:4b | cpu | 4105.6 | 0.0 | 0.833 | 4489.0 |
| gemma3:4b | nvidia | 463.0 | 0.0 | 0.833 | 896.3 |
| gemma4:12b | cpu | 4590.7 | 0.0 | 0.833 | 4974.0 |
| gemma4:12b | nvidia | 491.7 | 0.0 | 0.833 | 925.0 |
| gpt-oss:20b | cpu | 4251.7 | 0.0 | 0.833 | 4635.0 |
| gpt-oss:20b | nvidia | 1221.1 | 0.0 | 0.667 | 1737.8 |
| granite4.2:3b | cpu | 4656.6 | 0.0 | 0.833 | 5040.0 |
| granite4.2:3b | nvidia | 369.8 | 0.0 | 0.833 | 803.1 |
| granite4.2:8b | cpu | 3897.1 | 0.0 | 0.833 | 4280.5 |
| granite4.2:8b | nvidia | 405.9 | 0.0 | 0.833 | 839.2 |
| lfm2.5:8b | cpu | 5104.9 | 0.0 | 0.833 | 5488.2 |
| lfm2.5:8b | nvidia | 693.4 | 0.0 | 0.833 | 1126.8 |
| llama2-uncensored:latest | cpu | 14631.9 | 0.0 | 0.833 | 15015.2 |
| llama2-uncensored:latest | nvidia | 461.8 | 0.0 | 0.833 | 895.2 |
| llama3.1:8b | cpu | 5050.4 | 0.0 | 0.833 | 5433.7 |
| llama3.1:8b | nvidia | 1317.3 | 0.0 | 0.667 | 1833.9 |
| llama3.2:3b | cpu | 4600.6 | 0.0 | 0.833 | 4983.9 |
| llama3.2:3b | nvidia | 1800.8 | 0.0 | 0.667 | 2317.5 |
| llama3:8b | cpu | 4441.3 | 0.0 | 0.833 | 4824.7 |
| llama3:8b | nvidia | 1220.0 | 0.0 | 0.667 | 1736.7 |
| llama3:latest | cpu | 5042.9 | 0.0 | 0.833 | 5426.2 |
| llama3:latest | nvidia | 551.5 | 0.0 | 0.833 | 984.9 |
| ministral-3:3b | cpu | 5494.9 | 0.0 | 0.833 | 5878.3 |
| ministral-3:3b | nvidia | 657.6 | 0.167 | 1.0 | 957.6 |
| ministral-3:8b | cpu | 14446.5 | 0.0 | 0.833 | 14829.8 |
| ministral-3:8b | nvidia | 405.7 | 0.0 | 0.833 | 839.0 |
| mistral-nemo:latest | cpu | 4544.5 | 0.167 | 1.0 | 4794.5 |
| mistral-nemo:latest | nvidia | 1221.1 | 0.0 | 0.667 | 1737.8 |
| mistral-small:24b | cpu | 5233.4 | 0.0 | 0.833 | 5616.8 |
| mistral-small:24b | nvidia | 527.9 | 0.0 | 0.833 | 961.2 |
| nemotron-3-nano:4b | cpu | 4533.2 | 0.0 | 0.833 | 4916.5 |
| nemotron-3-nano:4b | nvidia | 473.6 | 0.0 | 0.833 | 906.9 |
| neural-chat:latest | cpu | 4310.0 | 0.0 | 0.833 | 4693.3 |
| neural-chat:latest | nvidia | 425.8 | 0.0 | 0.833 | 859.1 |
| nous-hermes2:latest | cpu | 4909.1 | 0.0 | 0.833 | 5292.4 |
| nous-hermes2:latest | nvidia | 696.3 | 0.0 | 0.833 | 1129.7 |
| openhermes:latest | cpu | 4604.5 | 0.167 | 1.0 | 4854.5 |
| openhermes:latest | nvidia | 1239.0 | 0.0 | 0.667 | 1755.6 |
| phi3:mini | cpu | 4399.9 | 0.0 | 0.833 | 4783.2 |
| phi3:mini | nvidia | 418.1 | 0.0 | 0.833 | 851.4 |
| phi4-mini:latest | cpu | 4578.1 | 0.0 | 0.833 | 4961.5 |
| phi4-mini:latest | nvidia | 513.8 | 0.0 | 0.833 | 947.1 |
| qwen2.5-coder-14b-agent:latest | cpu | 4823.5 | 0.0 | 0.833 | 5206.8 |
| qwen2.5-coder-14b-agent:latest | nvidia | 462.7 | 0.0 | 0.833 | 896.1 |
| qwen2.5-coder-32b-64k:latest | cpu | 4357.1 | 0.0 | 0.833 | 4740.4 |
| qwen2.5-coder-32b-64k:latest | nvidia | 480.6 | 0.0 | 0.833 | 914.0 |
| qwen2.5-coder:1.5b-base | cpu | 4320.8 | 0.0 | 0.833 | 4704.1 |
| qwen2.5-coder:1.5b-base | nvidia | 459.6 | 0.0 | 0.833 | 892.9 |
| qwen2.5-coder:14b | cpu | 4614.2 | 0.0 | 0.833 | 4997.5 |
| qwen2.5-coder:14b | nvidia | 524.0 | 0.0 | 0.833 | 957.4 |
| qwen2.5-coder:32b | cpu | 3846.3 | 0.0 | 0.833 | 4229.7 |
| qwen2.5-coder:32b | nvidia | 468.1 | 0.0 | 0.833 | 901.4 |
| qwen2.5-coder:7b | cpu | 5055.7 | 0.0 | 0.833 | 5439.0 |
| qwen2.5-coder:7b | nvidia | 402.5 | 0.0 | 0.833 | 835.9 |
| qwen2.5:14b | cpu | 4269.2 | 0.0 | 0.833 | 4652.6 |
| qwen2.5:14b | nvidia | 423.4 | 0.0 | 0.833 | 856.8 |
| qwen2.5:3b | cpu | 3880.4 | 0.0 | 0.833 | 4263.7 |
| qwen2.5:3b | nvidia | 456.0 | 0.0 | 0.833 | 889.3 |
| qwen2.5:7b | cpu | 4491.8 | 0.0 | 0.833 | 4875.1 |
| qwen2.5:7b | nvidia | 447.3 | 0.0 | 0.833 | 880.7 |
| qwen3.5:4b | cpu | 4639.4 | 0.0 | 0.833 | 5022.7 |
| qwen3.5:4b | nvidia | 455.0 | 0.0 | 0.833 | 888.3 |
| qwen3.5:9b | cpu | 4380.9 | 0.0 | 0.833 | 4764.2 |
| qwen3.5:9b | nvidia | 415.0 | 0.0 | 0.833 | 848.4 |
| qwen3.6:27b | cpu | 6313.2 | 0.167 | 1.0 | 6563.2 |
| qwen3.6:27b | nvidia | 412.9 | 0.0 | 0.833 | 846.2 |
| qwen3:1.7b | cpu | 4978.9 | 0.0 | 0.833 | 5362.3 |
| qwen3:1.7b | nvidia | 519.1 | 0.0 | 0.833 | 952.4 |
| qwen3:14b | cpu | 4995.4 | 0.0 | 0.833 | 5378.8 |
| qwen3:14b | nvidia | 1630.7 | 0.167 | 0.833 | 2014.1 |
| qwen3:4b | cpu | 5011.3 | 0.0 | 0.833 | 5394.6 |
| qwen3:4b | nvidia | 530.7 | 0.0 | 0.833 | 964.1 |
| qwen3:8b | cpu | 4096.2 | 0.0 | 0.833 | 4479.5 |
| qwen3:8b | nvidia | 488.3 | 0.0 | 0.833 | 921.6 |
| qwen3:latest | cpu | 4617.8 | 0.0 | 0.833 | 5001.1 |
| qwen3:latest | nvidia | 544.2 | 0.0 | 0.833 | 977.5 |
