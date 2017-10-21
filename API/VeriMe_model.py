import tensorflow as tf
import numpy as np


def _variable_on_cpu(name, shape, initializer):
    """Helper to create a Variable stored on CPU memory.
    Args:
      name: name of the variable
      shape: list of ints
      initializer: initializer for Variable
    Returns:
      Variable Tensor
    """
    with tf.device('/cpu:0'):
        var = tf.get_variable(name, shape, initializer=initializer, dtype=tf.float32)
    return var


def _variable_with_weight_decay(name, shape, stddev, wd):
    """Helper to create an initialized Variable with weight decay.
    Note that the Variable is initialized with a truncated normal distribution.
    A weight decay is added only if one is specified.
    Args:
      name: name of the variable
      shape: list of ints
      stddev: standard deviation of a truncated Gaussian
      wd: add L2Loss weight decay multiplied by this float. If None, weight
          decay is not added for this Variable.
    Returns:
      Variable Tensor
    """
    dtype = tf.float32
    # if FLAGS.use_fp16 else tf.float32
    var = _variable_on_cpu(
        name,
        shape,
        tf.truncated_normal_initializer(stddev=stddev, dtype=dtype))
    if wd is not None:
        weight_decay = tf.mul(tf.nn.l2_loss(var), wd, name='weight_loss')
        tf.add_to_collection('losses', weight_decay)
    return var

class CNN_model():

    def __init__(self, feature_size, num_classes, image_width, image_height):

        self.x = tf.placeholder('float', shape=[None, feature_size], name='input')
        x_image = tf.reshape(self.x, [-1, image_width, image_height, 1])

        self.y_ = tf.placeholder('float', shape=[None, num_classes], name='label')

        with tf.variable_scope('conv1', reuse=None) as scope:

            kernel = _variable_with_weight_decay(name='weights',
                                                 shape=[5, 5, 1, 64],
                                                 stddev=5e-2,
                                                 wd=0.0)
            conv = tf.nn.conv2d(x_image, kernel, [1, 1, 1, 1], padding='SAME')
            # conv = conv2d(x_image, kernel)
            biases = _variable_on_cpu('biases', [64], tf.constant_initializer(0.0))
            pre_activation = tf.nn.bias_add(conv, biases)
            conv1 = tf.nn.relu(pre_activation, name=scope.name)
            # _activation_summary(conv1)

        # pool1
        self.pool1 = tf.nn.max_pool(conv1, ksize=[1, 3, 3, 1], strides=[1, 2, 2, 1],
                                    padding='SAME', name='pool1')
        # norm1
        self.norm1 = tf.nn.lrn(self.pool1, 4, bias=1.0, alpha=0.001 / 9.0, beta=0.75,
                               name='norm1')


        # conv2
        with tf.variable_scope('conv2') as scope:
            kernel = _variable_with_weight_decay(name='weights',
                                                 shape=[5, 5, 64, 64],
                                                 stddev=5e-2,
                                                 wd=0.0)
            conv = tf.nn.conv2d(self.norm1, kernel, [1, 1, 1, 1], padding='SAME')
            biases = _variable_on_cpu('biases', [64], tf.constant_initializer(0.1))
            pre_activation = tf.nn.bias_add(conv, biases)
            conv2 = tf.nn.relu(pre_activation, name=scope.name)
            # _activation_summary(conv2)

        # norm2
        self.norm2 = tf.nn.lrn(conv2, 4, bias=1.0, alpha=0.001 / 9.0, beta=0.75,
                               name='norm2')
        # pool2
        self.pool2 = tf.nn.max_pool(self.norm2, ksize=[1, 3, 3, 1],
                                    strides=[1, 2, 2, 1], padding='SAME', name='pool2')

        full_feature_size_width = image_width // 4
        full_feature_size_height = image_height // 4

        # local3
        with tf.variable_scope('local3') as scope:
            # Move everything into depth so we can perform a single matrix multiply.
            # reshape = tf.reshape(pool2, [batch_size, -1])
            # dim = reshape.get_shape()[1].value
            reshape = tf.reshape(self.pool2, [-1, full_feature_size_width * full_feature_size_height * 64])
            weights = _variable_with_weight_decay('weights',
                                                  shape=[full_feature_size_width * full_feature_size_height * 64, 384],
                                                  stddev=0.04, wd=0.004)
            biases = _variable_on_cpu('biases', [384], tf.constant_initializer(0.1))
            local3 = tf.nn.relu(tf.matmul(reshape, weights) + biases, name=scope.name)
            # _activation_summary(local3)

        # local4
        with tf.variable_scope('local4') as scope:
            weights = _variable_with_weight_decay('weights', shape=[384, 192],
                                                  stddev=0.04, wd=0.004)
            biases = _variable_on_cpu('biases', [192], tf.constant_initializer(0.1))
            local4 = tf.nn.relu(tf.matmul(local3, weights) + biases, name=scope.name)
            # _activation_summary(local4)

            # linear layer(WX + b),
            # We don't apply softmax here because
            # tf.nn.sparse_softmax_cross_entropy_with_logits accepts the unscaled logits
            # and performs the softmax internally for efficiency.
        with tf.variable_scope('softmax_linear') as scope:
            weights = _variable_with_weight_decay('weights', [192, num_classes],
                                                  stddev=1 / 192.0, wd=0.0)
            biases = _variable_on_cpu('biases', [num_classes], tf.constant_initializer(0.0))
            self.y = tf.add(tf.matmul(local4, weights), biases, name=scope.name)
            # _activation_summary(softmax_linear)

        with tf.name_scope("loss"):
            self.cross_entropy = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(self.y, self.y_))

        with tf.name_scope("accuracy"):
            self.true_label = tf.argmax(self.y_, 1)
            self.predict_label = tf.argmax(self.y, 1)
            correct_prediction = tf.equal(self.true_label, self.predict_label)
            self.accuracy = tf.reduce_mean(tf.cast(correct_prediction, 'float'))
