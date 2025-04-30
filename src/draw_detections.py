import config
import cv2
from typing import Dict
from cv2.typing import MatLike


class DrawDetections:
    def __init__(self):
        self.classes_detected = []

    def draw(self, frame: MatLike, results: list, model_names: Dict[int, str]):
        """Draws bounding boxes and labels on the frame."""

        detected_objects = 0

        for box in results[0].boxes.data:
            x1, y1, x2, y2, confidence, class_id_tensor = box
            confidence = float(confidence)
            class_id = int(class_id_tensor)

            if confidence >= config.CONFIDENCE_THRESHOLD:
                if model_names.get(class_id) not in self.classes_detected:
                    self.classes_detected.append(model_names.get(class_id))

                x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])

                if class_id % 2 == 0:
                    color = (0, 255, 0)
                else:
                    color = (255, 0, 0)

                detected_objects += 1
                detected_class_name = model_names.get(class_id, f"ID: {class_id}")
                label = f"{detected_class_name}: {confidence:.2f}"

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness=2)

                label_size, base_line = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                y1_label = max(y1, label_size[1] + 10)
                cv2.rectangle(
                    frame, (x1, y1_label - label_size[1] - 10), (x1 + label_size[0], y1_label - base_line), color, cv2.FILLED
                )
                cv2.putText(frame, label, (x1, y1_label - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        return frame, detected_objects
