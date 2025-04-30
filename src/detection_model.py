import config
import torch
from ultralytics import YOLO


class DetectionModel:
    def __init__(self):
        self.__get_device()

    def load(self):
        try:
            model = YOLO(config.MODEL_NAME).to(self.device)
            model(torch.zeros(1, 3, 640, 640).to(self.device))

            return model
        except Exception as e:
            return None

    def __get_device(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Chosen device: {self.device}")
