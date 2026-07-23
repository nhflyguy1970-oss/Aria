# NLU Classifier Benchmark

**Model:** `llama3.2-vision:11b`
**Device:** `amd`
**Date:** 2026-07-23T10:16:30
**Average latency:** 989.4 ms
**Reason:** Lowest composite score (latency 989.4ms warm, accuracy 0%, JSON 83%). AMD GPU chosen as least disruptive dedicated classifier device.

| Model | Device | Warm ms | Accuracy | JSON | Score |
|-------|--------|---------|----------|------|-------|
| llama3.2-vision:11b | amd | 989.4 | 0.0 | 0.833 | 1422.7 |
| qwen3:14b | amd | 989.5 | 0.0 | 0.833 | 1422.9 |
| qwen2.5-coder:1.5b-base | amd | 990.8 | 0.0 | 0.833 | 1424.1 |
| qwen2.5:14b | amd | 992.9 | 0.0 | 0.833 | 1426.2 |
| qwen2.5-coder-14b-agent:latest | amd | 997.8 | 0.0 | 0.833 | 1431.2 |
| qwen3:1.7b | amd | 1001.8 | 0.0 | 0.833 | 1435.1 |
| qwen2.5:3b | amd | 1002.2 | 0.0 | 0.833 | 1435.5 |
| llama3:8b | amd | 1002.6 | 0.0 | 0.833 | 1436.0 |
| qwen2.5vl:7b | amd | 1003.5 | 0.0 | 0.833 | 1436.8 |
| qwen2.5-coder:32b | amd | 1006.2 | 0.0 | 0.833 | 1439.5 |
| qwen2.5:7b | amd | 1006.7 | 0.0 | 0.833 | 1440.0 |
| qwen2.5-coder:7b | amd | 1008.0 | 0.0 | 0.833 | 1441.3 |
| moondream:latest | amd | 1016.4 | 0.0 | 0.833 | 1449.7 |
| deepseek-coder:latest | amd | 1024.3 | 0.0 | 0.833 | 1457.7 |
| dolphin-mistral:latest | amd | 1025.1 | 0.0 | 0.833 | 1458.4 |
| qwen3:latest | amd | 1029.9 | 0.0 | 0.833 | 1463.2 |
| gemma3:4b | amd | 1034.4 | 0.0 | 0.833 | 1467.8 |
| deepseek-r1:7b | amd | 1035.6 | 0.0 | 0.833 | 1468.9 |
| llava:13b | amd | 1037.4 | 0.0 | 0.833 | 1470.8 |
| qwen2.5-coder-32b-64k:latest | amd | 1038.1 | 0.0 | 0.833 | 1471.4 |
| gemma3:12b | amd | 1038.5 | 0.0 | 0.833 | 1471.8 |
| nous-hermes2:latest | amd | 1039.7 | 0.0 | 0.833 | 1473.0 |
| mistral-small:24b | amd | 1040.8 | 0.0 | 0.833 | 1474.1 |
| llama2-uncensored:latest | amd | 1043.0 | 0.0 | 0.833 | 1476.3 |
| phi3:mini | amd | 1045.3 | 0.0 | 0.833 | 1478.6 |
| deepseek-coder-v2:latest | amd | 1059.3 | 0.0 | 0.833 | 1492.6 |
| devstral:latest | amd | 1074.1 | 0.0 | 0.833 | 1507.5 |
| nomic-embed-text:latest | amd | 1082.4 | 0.0 | 0.833 | 1515.8 |
| llava:7b | amd | 1088.1 | 0.0 | 0.833 | 1521.4 |
| qwen2.5-coder:32b | cpu | 4748.3 | 0.0 | 0.833 | 5131.7 |
| qwen3:1.7b | cpu | 4752.3 | 0.0 | 0.833 | 5135.6 |
| qwen2.5:14b | cpu | 4758.1 | 0.0 | 0.833 | 5141.4 |
| qwen3:latest | cpu | 4765.5 | 0.0 | 0.833 | 5148.8 |
| qwen2.5-coder:1.5b-base | cpu | 4780.9 | 0.0 | 0.833 | 5164.2 |
| qwen2.5-coder:14b | cpu | 4841.6 | 0.0 | 0.833 | 5224.9 |
| qwen2.5:7b | cpu | 4842.5 | 0.0 | 0.833 | 5225.8 |
| qwen3.5:9b | cpu | 4914.4 | 0.0 | 0.833 | 5297.7 |
| qwen2.5-coder-32b-64k:latest | cpu | 4952.9 | 0.0 | 0.833 | 5336.2 |
| llama3:latest | cpu | 5036.0 | 0.0 | 0.833 | 5419.3 |
| gemma3:12b | cpu | 5040.1 | 0.0 | 0.833 | 5423.4 |
| llama3.2-vision:11b | cpu | 5124.3 | 0.0 | 0.833 | 5507.6 |
| llama3.1:8b | cpu | 5171.6 | 0.0 | 0.833 | 5554.9 |
| llava:13b | cpu | 5198.5 | 0.0 | 0.833 | 5581.8 |
| dolphin3:latest | cpu | 5227.2 | 0.0 | 0.833 | 5610.6 |
| deepseek-r1:7b | cpu | 5236.6 | 0.0 | 0.833 | 5619.9 |
| mistral-nemo:latest | cpu | 5238.4 | 0.0 | 0.833 | 5621.7 |
| nomic-embed-text:latest | cpu | 5248.4 | 0.0 | 0.833 | 5631.7 |
| deepseek-coder-v2:latest | cpu | 5268.6 | 0.0 | 0.833 | 5651.9 |
| dolphin-mistral:latest | cpu | 5284.7 | 0.0 | 0.833 | 5668.0 |
| deepseek-coder-v2:16b | cpu | 5288.3 | 0.0 | 0.833 | 5671.6 |
| gemma3:4b | cpu | 5291.6 | 0.0 | 0.833 | 5674.9 |
| openhermes:latest | cpu | 5292.3 | 0.0 | 0.833 | 5675.6 |
| deepseek-r1:14b | cpu | 5324.6 | 0.0 | 0.833 | 5707.9 |
| phi3:mini | cpu | 5368.4 | 0.0 | 0.833 | 5751.7 |
| mistral-small:24b | cpu | 5381.9 | 0.0 | 0.833 | 5765.2 |
| neural-chat:latest | cpu | 5448.2 | 0.0 | 0.833 | 5831.5 |
| coder-stable:latest | cpu | 7373.8 | 0.0 | 0.833 | 7757.1 |
| qwen2.5vl:7b | cpu | 9673.1 | 0.0 | 0.833 | 10056.4 |
| llama3:8b | cpu | 9682.9 | 0.0 | 0.833 | 10066.2 |
| qwen3:14b | cpu | 9691.2 | 0.0 | 0.833 | 10074.5 |
| qwen2.5-coder:7b | cpu | 9844.3 | 0.0 | 0.833 | 10227.6 |
| qwen2.5:3b | cpu | 9854.6 | 0.0 | 0.833 | 10237.9 |
| qwen2.5-coder-14b-agent:latest | cpu | 9953.2 | 0.0 | 0.833 | 10336.5 |
| nous-hermes2:latest | cpu | 10203.7 | 0.0 | 0.833 | 10587.0 |
| deepseek-coder:latest | cpu | 10215.5 | 0.0 | 0.833 | 10598.9 |
| llava:7b | cpu | 10340.2 | 0.0 | 0.833 | 10723.5 |
| devstral:latest | cpu | 10432.6 | 0.0 | 0.833 | 10815.9 |
| llama2-uncensored:latest | cpu | 10455.4 | 0.0 | 0.833 | 10838.7 |
| moondream:latest | cpu | 10969.5 | 0.0 | 0.833 | 11352.9 |
| qwen3.5:9b | amd | 13440.0 | 0.0 | 0.833 | 13873.4 |
| qwen2.5-coder:14b | amd | 13487.2 | 0.0 | 0.833 | 13920.5 |
| llama3:latest | amd | 13745.3 | 0.0 | 0.833 | 14178.6 |
| neural-chat:latest | amd | 13805.2 | 0.0 | 0.833 | 14238.5 |
| deepseek-r1:14b | amd | 13901.9 | 0.0 | 0.833 | 14335.2 |
| openhermes:latest | amd | 13971.6 | 0.0 | 0.833 | 14405.0 |
| mistral-nemo:latest | amd | 14054.0 | 0.0 | 0.833 | 14487.3 |
| deepseek-coder-v2:16b | amd | 14107.0 | 0.0 | 0.833 | 14540.3 |
| llama3.1:8b | amd | 14210.9 | 0.0 | 0.833 | 14644.2 |
| dolphin3:latest | amd | 27067.2 | 0.0 | 0.833 | 27500.5 |
| coder-stable:latest | amd | 54349.6 | 0.0 | 0.833 | 54782.9 |
