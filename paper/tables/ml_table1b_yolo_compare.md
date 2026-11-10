**Table 1b**

*Detector Sizes Compared; Selection by Validation mAP@50*

| Model | Params (M) | Val mAP@50 | Test mAP@50 | Test precision | Test recall | Selected |
|:--|--:|--:|--:|--:|--:|:--|
| baseline_yolov8n | 3.1 | 0.993 | 0.849 | 0.880 | 0.883 |  |
| yolo11s | 9.4 | 0.993 | 0.882 | 0.892 | 0.917 |  |
| yolov8s | 11.1 | 0.994 | 0.876 | 0.900 | 0.903 | yes |

*Note.* The model was chosen on validation images (2022 dates, training terminals) only. Test columns are reported for every model for transparency and did not influence the choice.
