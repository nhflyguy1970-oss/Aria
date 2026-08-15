# NLU Classifier Benchmark

**Model:** `qwen3:14b`
**Device:** `nvidia`
**Date:** 2026-07-30T18:50:01
**Average latency:** 730.0 ms
**Reason:** Lowest composite score (latency 730.0ms warm, accuracy 0%, JSON 83%). NVIDIA GPU chosen based on measured lowest classifier latency.

| Model | Device | Warm ms | Accuracy | JSON | Score |
|-------|--------|---------|----------|------|-------|
| qwen3:14b | nvidia | 730.0 | 0.0 | 0.833 | 1163.3 |
| qwen2.5-coder:7b | nvidia | 730.3 | 0.0 | 0.833 | 1163.6 |
| qwen2.5-coder-14b-agent:latest | nvidia | 730.8 | 0.0 | 0.833 | 1164.1 |
| qwen2.5:7b | nvidia | 731.5 | 0.0 | 0.833 | 1164.8 |
| llama3:8b | nvidia | 733.4 | 0.0 | 0.833 | 1166.8 |
| llama3.1:8b | nvidia | 733.9 | 0.0 | 0.833 | 1167.2 |
| qwen2.5-coder:14b | nvidia | 734.0 | 0.0 | 0.833 | 1167.3 |
| qwen3.5:9b | nvidia | 734.0 | 0.0 | 0.833 | 1167.4 |
| dolphin-mistral:latest | nvidia | 735.0 | 0.0 | 0.833 | 1168.3 |
| deepseek-r1:14b | nvidia | 735.7 | 0.0 | 0.833 | 1169.0 |
| mistral-small:24b | nvidia | 735.7 | 0.0 | 0.833 | 1169.0 |
| qwen3:latest | nvidia | 735.7 | 0.0 | 0.833 | 1169.1 |
| qwen2.5-coder-32b-64k:latest | nvidia | 738.2 | 0.0 | 0.833 | 1171.5 |
| dolphin3:latest | nvidia | 738.4 | 0.0 | 0.833 | 1171.7 |
| nous-hermes2:latest | nvidia | 739.0 | 0.0 | 0.833 | 1172.3 |
| mistral-nemo:latest | nvidia | 739.8 | 0.0 | 0.833 | 1173.2 |
| devstral:latest | nvidia | 740.6 | 0.0 | 0.833 | 1173.9 |
| openhermes:latest | nvidia | 741.2 | 0.0 | 0.833 | 1174.5 |
| qwen2.5-coder:32b | nvidia | 744.2 | 0.0 | 0.833 | 1177.6 |
| qwen2.5:14b | nvidia | 744.4 | 0.0 | 0.833 | 1177.7 |
| gemma3:4b | nvidia | 748.9 | 0.0 | 0.833 | 1182.2 |
| gemma3:12b | nvidia | 750.5 | 0.0 | 0.833 | 1183.9 |
| deepseek-r1:7b | nvidia | 765.9 | 0.0 | 0.833 | 1199.2 |
| deepseek-coder-v2:16b | nvidia | 772.0 | 0.0 | 0.833 | 1205.3 |
| deepseek-coder:latest | nvidia | 774.7 | 0.0 | 0.833 | 1208.1 |
| qwen3:1.7b | nvidia | 784.6 | 0.0 | 0.833 | 1217.9 |
| deepseek-coder-v2:latest | nvidia | 784.7 | 0.0 | 0.833 | 1218.0 |
| phi3:mini | nvidia | 788.5 | 0.0 | 0.833 | 1221.9 |
| qwen2.5:3b | nvidia | 791.3 | 0.0 | 0.833 | 1224.6 |
| llama2-uncensored:latest | nvidia | 796.4 | 0.0 | 0.833 | 1229.7 |
| llama3:latest | nvidia | 797.2 | 0.0 | 0.833 | 1230.5 |
| neural-chat:latest | nvidia | 798.3 | 0.0 | 0.833 | 1231.6 |
| qwen2.5-coder:1.5b-base | nvidia | 806.1 | 0.0 | 0.833 | 1239.4 |
| coder-stable:latest | nvidia | 853.9 | 0.0 | 0.833 | 1287.2 |
| qwen2.5-coder:7b | cpu | 4297.7 | 0.0 | 0.833 | 4681.0 |
| phi3:mini | cpu | 4302.5 | 0.0 | 0.833 | 4685.8 |
| qwen2.5-coder:1.5b-base | cpu | 4335.5 | 0.0 | 0.833 | 4718.8 |
| qwen3:14b | cpu | 4342.2 | 0.0 | 0.833 | 4725.6 |
| qwen2.5-coder-32b-64k:latest | cpu | 4343.5 | 0.0 | 0.833 | 4726.8 |
| dolphin3:latest | cpu | 4360.5 | 0.0 | 0.833 | 4743.8 |
| qwen2.5-coder:32b | cpu | 4374.7 | 0.0 | 0.833 | 4758.1 |
| qwen2.5:7b | cpu | 4376.2 | 0.0 | 0.833 | 4759.5 |
| gemma3:4b | cpu | 4399.5 | 0.0 | 0.833 | 4782.8 |
| devstral:latest | cpu | 4401.9 | 0.0 | 0.833 | 4785.2 |
| llama3:8b | cpu | 4406.9 | 0.0 | 0.833 | 4790.2 |
| openhermes:latest | cpu | 4410.0 | 0.0 | 0.833 | 4793.4 |
| qwen2.5:3b | cpu | 4434.6 | 0.0 | 0.833 | 4817.9 |
| deepseek-r1:7b | cpu | 4436.7 | 0.0 | 0.833 | 4820.1 |
| mistral-small:24b | cpu | 4438.0 | 0.0 | 0.833 | 4821.3 |
| neural-chat:latest | cpu | 4460.7 | 0.0 | 0.833 | 4844.0 |
| llama3:latest | cpu | 4467.8 | 0.0 | 0.833 | 4851.2 |
| llama2-uncensored:latest | cpu | 4478.8 | 0.0 | 0.833 | 4862.1 |
| dolphin-mistral:latest | cpu | 4490.9 | 0.0 | 0.833 | 4874.3 |
| qwen3:1.7b | cpu | 4506.2 | 0.0 | 0.833 | 4889.5 |
| gemma3:12b | cpu | 4526.6 | 0.0 | 0.833 | 4910.0 |
| qwen2.5-coder-14b-agent:latest | cpu | 4532.8 | 0.0 | 0.833 | 4916.1 |
| qwen3.5:9b | cpu | 4576.3 | 0.0 | 0.833 | 4959.6 |
| deepseek-r1:14b | cpu | 4612.8 | 0.0 | 0.833 | 4996.2 |
| mistral-nemo:latest | cpu | 4615.8 | 0.0 | 0.833 | 4999.1 |
| llama3.1:8b | cpu | 4661.1 | 0.0 | 0.833 | 5044.4 |
| qwen3:latest | cpu | 4678.2 | 0.0 | 0.833 | 5061.5 |
| nous-hermes2:latest | cpu | 4679.9 | 0.0 | 0.833 | 5063.3 |
| deepseek-coder-v2:16b | cpu | 4682.5 | 0.0 | 0.833 | 5065.8 |
| deepseek-coder-v2:latest | cpu | 4862.7 | 0.0 | 0.833 | 5246.0 |
| qwen2.5-coder:14b | cpu | 4877.3 | 0.0 | 0.833 | 5260.6 |
| qwen2.5:14b | cpu | 4899.6 | 0.0 | 0.833 | 5283.0 |
| deepseek-coder:latest | cpu | 5189.8 | 0.0 | 0.833 | 5573.1 |
| coder-stable:latest | cpu | 8051.8 | 0.0 | 0.833 | 8435.2 |
