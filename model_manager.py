import cv2
import numpy as np
import tensorflow as tf


class ModelManager:

    def __init__(self):

        print("Loading eye model...")
        self.eye_model = tf.keras.models.load_model(
            "eye_model.keras"
        )

        print("Loading yawn model...")
        self.yawn_model = tf.keras.models.load_model(
            "best_yawn_model.keras"
        )

        print("Models loaded successfully.")


    def prepare(self, image):

        if image is None or image.size == 0:
            return None

        # OpenCV BGR -> RGB
        image = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2RGB
        )

        image = cv2.resize(
            image,
            (224, 224)
        )

        image = image.astype(
            np.float32
        )

        # IMPORTANT FIX:
        # MobileNetV2 preprocessing
        #
        # converts:
        # 0..255
        #
        # into approximately:
        # -1..1

        image = tf.keras.applications.mobilenet_v2.preprocess_input(
            image
        )

        image = np.expand_dims(
            image,
            axis=0
        )

        return image


    def predict_eye(self, eye):

        prepared = self.prepare(
            eye
        )

        if prepared is None:
            return None

        prediction = self.eye_model.predict(
            prepared,
            verbose=0
        )

        return float(
            prediction[0][0]
        )


    def predict_yawn(self, face):

        prepared = self.prepare(
            face
        )

        if prepared is None:
            return None

        prediction = self.yawn_model.predict(
            prepared,
            verbose=0
        )

        return float(
            prediction[0][0]
        )