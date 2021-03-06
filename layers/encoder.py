import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import (
    Layer,
    MultiHeadAttention,
    LayerNormalization,
    Dense,
    Input,
)


tf.keras.utils.set_random_seed(42)


class TransformerEncoder(Layer):
    """
    Encoder part of and encoder-decoder architecture with attention mechanism

    Attributes
    ----------
    num_heads : int
                Number of heads for MultiHeadAttention

    embed_dim : int
                Dimension size used within embedding layer

    dense_units : int
                  Number of units will be used inside dense layer

    **kwargs : dict
               Remain key-value pairs for a keras.layers.Layer object

    Methods
    -------
    call(self, inputs, mask=None)
        Function used for computation, see keras docs for more information

    get_config(self)
        See https://keras.io/api/models/model_saving_apis/#getconfig-method

    Notes
    -----
    Also see https://keras.io/guides/making_new_layers_and_models_via_subclassing/

    """

    def __init__(self, num_heads, embed_dim, dense_units, **kwargs):
        super().__init__(**kwargs)

        self.num_heads = num_heads
        self.embed_dim = embed_dim
        self.dense_units = dense_units

        self.attention = MultiHeadAttention(num_heads=num_heads, key_dim=embed_dim)

        # also called as dense projections
        self.dense = Sequential(
            [
                Input(
                    shape=(None, embed_dim)
                ),  # shape=(batch_size * sequence_length (max_length in this case), embed_dim)
                Dense(dense_units, activation="relu"),
                # to be able concatenate outputs with inputs
                # output layer of dense projections should have same size with input dimension
                # embed_dim in this case
                Dense(embed_dim),
            ]
        )

        self.first_layer_norm = LayerNormalization()
        self.second_layer_norm = LayerNormalization()

        self.supports_masking = True

    def call(self, inputs, mask=None):
        if mask is not None:
            # The mask generated by Embedding layer will be 2D
            # but Attention layer expects mask to be 3D or 4D
            # so this operation adds a new axis around samples in the batch
            mask = mask[:, tf.newaxis, :]

        attention_output = self.attention(
            query=inputs, key=inputs, value=inputs, attention_mask=mask
        )
        proj_input = self.first_layer_norm(inputs + attention_output)
        proj_output = self.dense(proj_input)
        output = self.second_layer_norm(proj_input + proj_output)

        return output

    # To be able save model in HDF5 format, get_config method has to be implemented
    # https://www.tensorflow.org/tutorials/keras/save_and_load#saving_custom_objects
    def get_config(self):
        config = super().get_config()

        config.update(
            {
                "num_heads": self.num_heads,
                "embed_dim": self.embed_dim,
                "dense_units": self.dense_units,
            }
        )

        return config
