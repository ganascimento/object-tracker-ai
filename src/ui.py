import streamlit as st
import torch
import os
import tempfile
import cv2
import config
import numpy as np
from detection_model import DetectionModel
from draw_detections import DrawDetections
from mode_enum import CaptureMode

torch.classes.__path__ = [os.path.dirname(os.path.abspath(torch.__file__))]


class UI:
    def __init__(self):
        if "model" not in st.session_state:
            st.session_state.model = None

        if "mode" not in st.session_state:
            st.session_state.mode = CaptureMode.UPLOAD

        self.load_model()
        self.draw_detections = DrawDetections()

    def load_model(self):
        if st.session_state.model is None:
            st.session_state.model = DetectionModel().load()
            if st.session_state.model is None:
                st.error(f"Error to load model")

    def build(self):
        st.set_page_config(page_title="Object Tracker AI", layout="centered", page_icon="🧱")

        if st.session_state.model is None:
            return

        st.title("🧱 Object detector")
        st.markdown("#### Upload an image, video or take a photo to detect objects!")

        self.__build_sidebar()

        if st.session_state.mode == CaptureMode.UPLOAD:
            uploaded_file = st.file_uploader("Choose a file", type=config.IMAGE_EXTENSIONS + config.VIDEO_EXTENSIONS)
        elif st.session_state.mode == CaptureMode.WEB_CAM:
            uploaded_file = st.camera_input("Tire uma foto")

        if uploaded_file is None:
            return

        file_extension = os.path.splitext(uploaded_file.name)[-1].lower()
        file_extension = file_extension.replace(".", "")

        frame_placeholder = st.empty()
        grid = st.columns(2)
        count_metrics = grid[0].empty()

        if file_extension in config.IMAGE_EXTENSIONS:
            self.__detect_in_image(uploaded_file, frame_placeholder, count_metrics)
        elif file_extension in config.VIDEO_EXTENSIONS:
            self.__detect_in_video(uploaded_file, frame_placeholder, count_metrics)

        if len(self.draw_detections.classes_detected) > 0:
            st.markdown("### Class detecteds")
            for item in self.draw_detections.classes_detected:
                st.markdown(f" - {item}")

    def __load_temp_video(self, uploaded_file):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tfile:
            tfile.write(uploaded_file.read())
            st.success(f"Video uploaded: {uploaded_file.name}")
            return tfile.name

    def __build_sidebar(self):
        st.sidebar.markdown("🖼️ Upload video and image files to detect objects")
        st.sidebar.button("Upload file 🖼️", on_click=self.__select_mode_upload)

        st.sidebar.markdown("---")

        st.sidebar.markdown("📷 Take a picture with a webcam to detect objects")
        st.sidebar.button("Take a foto 📷", on_click=self.__select_mode_wbcam)

    def __detect_in_image(self, uploaded_file, frame_placeholder, count_metrics):
        try:
            image = cv2.imdecode(np.frombuffer(uploaded_file.read(), np.uint8), cv2.IMREAD_COLOR)
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = st.session_state.model(image_rgb, verbose=False)

            image_bgr, detected_objects = self.draw_detections.draw(image, results, st.session_state.model.names)
            image_display = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

            frame_placeholder.image(image_display, caption="Processed Image")
            count_metrics.metric("Detected objects", detected_objects)
        except Exception as e:
            st.error(f"An error occurred during processing: {e}")

    def __detect_in_video(self, uploaded_file, frame_placeholder, count_metrics):
        temp_video_path = self.__load_temp_video(uploaded_file)
        progress_bar = st.progress(0)

        try:
            capture = cv2.VideoCapture(temp_video_path)
            if not capture.isOpened():
                st.error("Error opening video file.")
                return

            total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
            st.info(f"Processing video with {total_frames} frames...")
            frame_count = 0

            while True:
                readed, frame = capture.read()
                if not readed:
                    break

                frame_count += 1
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = st.session_state.model(frame_rgb, verbose=False)

                frame_bgr, detected_objects = self.draw_detections.draw(frame, results, st.session_state.model.names)

                frame_display = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                frame_placeholder.image(frame_display, caption=f"Frame Processed {frame_count}")
                count_metrics.metric("Detected objects", detected_objects)

                progress_bar.progress(frame_count / total_frames)

            capture.release()
        except Exception as e:
            st.error(f"An error occurred during processing: {e}")
        finally:
            if "temp_video_path" in locals() and os.path.exists(temp_video_path):
                os.remove(temp_video_path)

    def __select_mode_upload(self):
        st.session_state.mode = CaptureMode.UPLOAD

    def __select_mode_wbcam(self):
        st.session_state.mode = CaptureMode.WEB_CAM
