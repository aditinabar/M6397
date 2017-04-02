
from __future__ import division

"""%TRAIN_RBM Trains a Restricted Boltzmann Machine using contrastive divergence
%
%   machine = train_rbm(X, h, type, eta, max_iter)
%
% Trains a first-order Restricted Boltzmann Machine on dataset "X".

%The RBM has h hidden nodes (default = 20).
%The training is performed by means of
% the contrastive divergence algorithm. The activation function that
% is applied in the hidden layer is specified by type. Possible values are
% "linear" and "sigmoid" (default = 'sigmoid').

%In the training of the RBM,
% the learning rate is determined by "eta" (default = 0.25).

%The maximum number of iterations can be specified through
%"max_iter" (default = 50).

%The trained RBM is returned in the "machine" struct.
%
% A Boltzmann Machine is a graphical model in which every node is
% connected to all other nodes, except to itself. The nodes are binary,
% i.e., they have either value -1 or 1. The model is similar to Hopfield
% networks, except for that its nodes are stochastic, using a logistic
% distribution. It can be shown that the Boltzmann Machine can be trained
% by means of an extremely simple update rule. However, training is in
% practice not feasible.
%
% In a Restricted Boltzmann Machine, the nodes are separated into visible
% and hidden nodes. The visible nodes are not connected to each other, and
% neither are the hidden nodes. When training a RBM, the same update rule
% can be used, however, the data is now clamped onto the visible nodes.
% This training procedure is called contrastive divergence. Alternatively,
% the visible nodes may be Gaussians instead of binary logistic nodes.
%

% This file is part of the Matlab Toolbox for Dimensionality Reduction v0.4b.
% The toolbox can be obtained from http://www.cs.unimaas.nl/l.vandermaaten
% You are free to use, change, or redistribute this code in any way you
% want for non-commercial purposes. However, it is appreciated if you
% maintain the name of the original author.
%
% (C) Laurens van der Maaten
% Maastricht University, 2007"""

import numpy as np
from keras.datasets import mnist


class rbm_matlab():
    """docstring for rbm_matlab"""
    def __init__(self, X, h=20, activation='sigmoid', eta=0.1, max_iter=100):

        # Process inputs
        self.images = X
        self.h = h
        self.activation = activation
        self.eta = eta
        self.max_iter = max_iter

        # Important parameters
        self.initial_momentum = 0.5     # momentum for first five iterations
        self.final_momentum = 0.9       # momentum for remaining iterations
        self.weight_cost = 0.0002       # costs of weight update

        # Initialize some variables
        self.input_size = self.images.shape[0]
        self.visible_units = self.images.shape[1]
        self.batch_size = 256
        self.W = np.random.randn(self.visible_units, self.h) * 0.1

        # hidden units biases:
        self.bias_upW = np.zeros((1, self.h))

        # visible units biases:
        self.bias_downW = np.zeros((1, self.visible_units))

        # gradient increments:
        self.deltaW = np.zeros((self.visible_units, self.h))
        self.deltaBias_upW = np.zeros((1, self.h))
        self.deltaBias_downW = np.zeros((1, self.visible_units))

    def images_to_vectors(self):
        """ We will normalize all values between 0 and 1 and we will
        flatten the 28x28 images into vectors of size 784. """
        self.x_train = self.x_train.astype('float32') / 255
        self.x_test = self.x_test.astype('float32') / 255
        self.x_train = self.x_train.reshape((len(self.x_train),
                                             np.prod(self.x_train.shape[1:])))
        self.x_test = self.x_test.reshape((len(self.x_test),
                                           np.prod(self.x_test.shape[1:])))

    def train_rbm(self):

        # Main loop
        for i in xrange(self.max_iter):

            # # Print progress
            if i % 10 == 0:
                print 'Iteration ' + str(iter) + '...'

            # # Set momentum
            if i <= 5:
                momentum = self.initial_momentum
            else:
                momentum = self.final_momentum

            # # Run for all mini-batches (= Gibbs sampling step 0)
            visitingOrder = np.random.randint(self.input_size)
            shuffled_Data = [self.images[i] for i in visitingOrder]

            for batch in xrange(1, self.input_size, self.batch_size):

                if batch + self.batch_size <= self.input_size:

                    # # Set values of visible nodes (= Gibbs sampling step 0)
                    visible_1 = float(shuffled_Data
                                      [batch: min(batch + self.batch_size - 1,
                                                  self.input_size), :])

                    # # Compute probabilities for hidden nodes
                    # (= Gibbs sampling step 0)
                    hidden_1 = 1 / (1 + np.exp(-(visible_1 * self.W +
                                    np.tile(self.bias_upW,
                                            [self.batch_size, 1]))))

                    # # Compute probabilities for visible nodes
                    # (= Gibbs sampling step 1)
                    visible_2 = 1 / (1 + np.exp(-(hidden_1 * self.W.T +
                                                  np.tile(self.bias_downW,
                                                          [self.batch_size,
                                                           1]))))

                    # # Compute probabilities for hidden nodes
                    # (= Gibbs sampling step 1)
                    if activation == 'sigmoid':
                        hidden_2 = 1 / (1 + np.exp(-(visible_2 * self.W +
                                        np.tile(self.bias_upW,
                                                [self.batch_size, 1]))))
                    else:
                        hidden_2 = visible_2 * self.W + np.tile(self.bias_upW,
                                                                [self.batch_size,
                                                                 1])

                    # # Now compute the weights update (contrastive divergence)
                    positive_products = hidden_1.T * visible_1
                    negative_products = hidden_2.T * visible_2
                    self.deltaW = (momentum * self.deltaW) +\
                                  (eta / self.batch_size) *\
                                  ((positive_products - negative_products).T -
                                   (self.weight_cost * self.W))

                    self.deltaBias_upW = (momentum * self.deltaBias_upW) +\
                        (eta / self.batch_size) * (np.sum(hidden_1, 1) -
                                                   np.sum(hidden_2, 1))

                    self.deltaBias_downW = momentum * self.deltaBias_downW +\
                        (eta / self.batch_size) * (np.sum(visible_1, 0) -
                                                   np.sum(visible_2, 0))

                    # # Divide by number of elements for linear activations
                    if activation != 'sigmoid':
                        self.deltaW = np.divide(self.deltaW,
                                                (self.visible_units * self.h))
                        self.deltaBias_upW = np.divide(self.deltaBias_upW,
                                                       self.deltaBias_upW.shape[0] *
                                                       self.deltaBias_upW.shape[1])
                        self.deltaBias_downW = np.divide(self.deltaBias_downW,
                                                    self.deltaBias_downW.shape[0] *
                                                    self.deltaBias_downW.shape[1])

                    # # Update the network weights
                    self.W += self.deltaW
                    self.bias_upW += self.deltaBias_upW
                    self.bias_downW += self.deltaBias_downW

        # % Return RBM
        # machine.W = W
        # machine.bias_upW = bias_upW
        # machine.bias_downW = bias_downW
        # machine.type = type

        # machine.tied = 'yes'
        # disp(' ')

