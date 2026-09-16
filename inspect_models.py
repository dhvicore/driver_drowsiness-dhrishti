import tensorflow as tf


MODEL_FILES = [
    "eye_model.keras",
    "eye_state_mobilenetv2.keras",
    "best_yawn_model.keras",
    "yawn_state_mobilenetv2.keras"
]


for path in MODEL_FILES:

    print("\n")
    print("=" * 70)
    print("MODEL:", path)
    print("=" * 70)

    try:
        model = tf.keras.models.load_model(path)

        print("INPUT :", model.input_shape)
        print("OUTPUT:", model.output_shape)

        print("\nFIRST 15 LAYERS:")

        for i, layer in enumerate(model.layers[:15]):

            print(
                i,
                layer.name,
                type(layer).__name__
            )

            try:
                print(
                    "   config:",
                    layer.get_config()
                )
            except:
                pass

    except Exception as e:

        print("ERROR:", e)