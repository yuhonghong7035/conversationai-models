"""Text Preprocessor.

Used to tokenize and then use embeddings for text.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from absl import app
from absl import flags

import nltk
import numpy as np
import tensorflow as tf
from tf_trainer import types
from typing import Tuple, Dict, Optional, List

FLAGS = flags.FLAGS


class TextPreprocessor():
  """Text Preprocessor.

  Takes an embedding and uses it to produce a preprocess method that can be
  called on texts to get its int representation. Also produces an embedding
  matrix to be used with a tensorflow graph.
  """

  def __init__(self, embeddings_path: types.Path) -> None:
    self._word_to_idx, self._embeddings_matrix, self._unknown_token = TextPreprocessor._get_word_idx_and_embeddings(
        embeddings_path)  # type: Tuple[Dict[str, int], np.ndarray, int]

  def word_to_idx_table(self) -> tf.contrib.lookup.HashTable:
    keys = list(self._word_to_idx.keys())
    values = list(self._word_to_idx.values())
    table = tf.contrib.lookup.HashTable(
        tf.contrib.lookup.KeyValueTensorInitializer(keys, values),
        self._unknown_token)
    return table

  def word_embeddings(self, trainable=False) -> tf.Variable:
    embeddings_shape = self._embeddings_matrix.shape
    initial_embeddings_matrix = tf.constant_initializer(self._embeddings_matrix)
    embeddings = tf.get_variable(
        name='word_embeddings',
        shape=embeddings_shape,
        initializer=initial_embeddings_matrix,
        trainable=trainable)
    return embeddings

  @staticmethod
  def _get_word_idx_and_embeddings(embeddings_path: types.Path,
                                   max_words: Optional[int] = None
                                  ) -> Tuple[Dict[str, int], np.ndarray, int]:
    """Generate word to idx mapping and word embeddings numpy array.

    Args:
      embeddings_path: Local, GCS, or HDFS path to embedding file. Each line
        should be a word and its vector representation separated by a space.
      max_words: The max number of words we are going to allow as part of the
        embedding.

    Returns:
      Tuple of vocab list, Numpy array of word embeddings with shape
      (vocab size, embedding size), and the unknown token.
    """
    word_to_idx = {}
    word_embeddings = []
    with tf.gfile.Open(embeddings_path, 'r') as f:
      for idx, line in enumerate(f):
        if max_words and idx >= max_words:
          break

        values = line.split()
        word = values[0]
        word_embedding = np.asarray(values[1:], dtype='float32')
        word_to_idx[word] = idx
        word_embeddings.append(word_embedding)

    unknown_token = len(word_embeddings)
    embeddings_matrix = np.asarray(word_embeddings, dtype=np.float32)
    embeddings_matrix = np.append(
        embeddings_matrix, [embeddings_matrix.mean(axis=0)], axis=0)
    return word_to_idx, embeddings_matrix, unknown_token
