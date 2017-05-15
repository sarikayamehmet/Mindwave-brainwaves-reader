import numpy as np

from keras.layers import LSTM, Dense, Dropout
from keras.models import Sequential
from keras.optimizers import RMSprop, SGD, Adam

np.set_printoptions(linewidth=200)
epochs = 5

batch_size = 5
dataset = np.genfromtxt('keirnAunonDataset.csv', delimiter=',', dtype=np.float32)


def calculate_max_sequence_length(dataset):
    max_seq_length = 0
    cur_seq_length = 0
    current_output = dataset[0][-5:]
    seqs = 1
    for row in dataset:
        o = row[-5:]
        if not np.array_equal(o, current_output):
            seqs += 1
            if cur_seq_length > max_seq_length:
                max_seq_length = cur_seq_length
            current_output = o
            cur_seq_length = 1
        else:
            cur_seq_length += 1
    return max_seq_length, seqs


def create_array_task(dataset, sequences):
    current_output = dataset[0][-5:]
    array_task = np.zeros(sequences, dtype=np.float32)
    line = 0
    i = 1
    for row in dataset:
        actual = row[-5:]

        if not np.array_equal(actual, current_output):
            array_task[i] = line
            i += 1
            current_output = actual
        line += 1
    return array_task


def k_fold_CV(dataset, folds):
    folds += 1
    fold_len = int(len(dataset) / folds)
    train_all = [[0 for x in range(folds)] for y in range(len(dataset) - fold_len)]
    validate_all = [[0 for x in range(folds)] for y in range(fold_len)]
    for i in range(1, folds):
        val_start = i * fold_len
        val_end = (i + 1) * fold_len
        train_all[i][:val_start] = dataset[:val_start - 1]
        train_all[i][val_start + 1:] = dataset[val_end + 1:]
        validate_all[i] = dataset[val_start:val_end]
    return train_all, validate_all


# train, val = k_fold_CV(dataset, 10)
# for i in range(1, 11):
#    np.savetxt('cross_validation/training_'+str(i)+'.csv', train[i], fmt='%i', delimiter=',')
#    np.savetxt('cross_validation/testing_'+str(i)+'.csv', val[i], fmt='%i', delimiter=',')


"""
It builds the network, defining its structure
"""


def create_model():
    model = Sequential()
    model.add(LSTM(11, stateful=True, return_sequences=True, batch_input_shape=(1, batch_size, 7)))
    model.add(LSTM(11, return_sequences=True))
    model.add(Dropout(.1))
    model.add(LSTM(11, return_sequences=True))
    model.add(Dropout(.1))
    model.add(LSTM(11))
    model.add(Dense(6))
    model.add(Dense(5, activation='softmax'))
    return model


def calculate_accuracy(set, model):
    m, n_test_sequences = calculate_max_sequence_length(set)
    indices = create_array_task(set, n_test_sequences)
    current_sequence_test = 0
    total_accuracy = 0
    for seqa in range(n_test_sequences - 1):
        starta = indices[current_sequence_test]
        enda = indices[current_sequence_test + 1]

        y_true = np.reshape(set[starta, -5:], (1, 5))
        # print('y è :', end='')
        # print(y_true)

        batch_x = np.expand_dims(set[starta:enda, 0:-5], 0)

        k = 0
        true_positives = 0
        while k < (enda - starta) / batch_size:
            batch_x = np.expand_dims(set[starta + k * batch_size:starta + ((k + 1) * batch_size), 0:-5], 0)
            output = model.predict_on_batch(batch_x)
            r_output = np.zeros((1, 5))
            r_output[0][np.argmax(output)] = 1
            if np.array_equal(r_output, y_true):
                true_positives += 1

            k += 1
        # print('accuracy : ',end='')
        total_accuracy += true_positives / ((enda - starta) / batch_size)
        model.reset_states()
        current_sequence_test += 1

    return total_accuracy / n_test_sequences


max_length, sequences = calculate_max_sequence_length(dataset)
sequences_indices = create_array_task(dataset, sequences=sequences)

test_set = dataset[sequences_indices[-8]:]
dataset = dataset[:sequences_indices[-8]]

max_length, sequences = calculate_max_sequence_length(dataset)

network = create_model()
print('Compiling model..')
opt = RMSprop(lr=0.0005)
network.compile(optimizer=opt, loss='categorical_crossentropy',
                metrics=['accuracy'])
print('Model compiled. Specs:')
network.summary()
"""

Simple train-test
for e in range(epochs):
    current_sequence = 0
    epoch_accuracy = 0
    for seq in range(sequences - 1):
        # print('sequenza'+str(current_sequence))
        start = sequences_indices[current_sequence]
        end = sequences_indices[current_sequence + 1]
        Train = dataset[start:end]
        y_true = np.reshape(Train[0][-4:], (1, 4))
        j = 0
        err = 0
        acc = 0
        while (j < (end - start) / 5):
            batch_x = Train[j * batch_size:(j + 1) * batch_size, 0:-4]
            batch_x = np.expand_dims(batch_x, 0)
            loss, accuracy = network.train_on_batch(batch_x, y_true)
            # print('Accuracy: '+str(accuracy))
            err += loss
            acc += accuracy
            #print('loss on batch '+str(j),end=' ')
            #print(':'+str(loss))
            j += 1
        # print('errore medio per questa sequenza '+str(err/((end-start)/5)))
        epoch_accuracy += acc / ((end - start) / 5)
        # print('accuratezza media per questa sequenza '+str(acc/((end-start)/5)))
        network.reset_states()
        current_sequence += 1
    print('accuratezza media per ques\'epoca sul training set: ' + str(epoch_accuracy / sequences))
    calculate_accuracy(test_set,network)
"""

"""
K-fold cross validation training
"""

for i in range(11):
    network = create_model()

    opt = RMSprop(lr=0.0005)
    network.compile(optimizer=opt, loss='categorical_crossentropy',
                    metrics=['accuracy'])
    print('Fold number: ' + str(i))
    X = np.genfromtxt('cross_validation/training_' + str(i) + '.csv', delimiter=',', dtype=np.float32)
    Y = np.genfromtxt('cross_validation/testing_' + str(i) + '.csv', delimiter=',', dtype=np.float32)
    for e in range(epochs):
        current_sequence = 0
        epoch_accuracy = 0
        print('Epoch :' + str(e))
        max_length, sequences = calculate_max_sequence_length(X)
        for seq in range(sequences - 1):
            # print('sequenza'+str(current_sequence))
            start = sequences_indices[current_sequence]     #324 * seqnum
            end = sequences_indices[current_sequence + 1]   #324 + 2500
            Train = X[start:end]
            y_true = np.reshape(Train[0][-5:], (1, 5))
            j = 0
            err = 0
            acc = 0
            while (j < (end - start) / batch_size):
                batch_x = Train[j * batch_size:(j + 1) * batch_size, 0:-5]
                batch_x = np.expand_dims(batch_x, 0)
                loss, accuracy = network.train_on_batch(batch_x, y_true)
                # print('Accuracy: '+str(accuracy))
                err += loss
                acc += accuracy
                # print('loss on batch '+str(j),end=' ')
                # print(':'+str(loss))
                j += 1
            # print('errore medio per questa sequenza '+str(err/((end-start)/5)))
            epoch_accuracy += acc / ((end - start) / batch_size)
            # print('accuratezza media per questa sequenza '+str(acc/((end-start)/5)))
            network.reset_states()
            current_sequence += 1
        print('accuratezza media per ques\'epoca sul training set: ' + str(epoch_accuracy / sequences))
        print('accuratezza sul test set :' + str(calculate_accuracy(Y, network)))

f = open('architecture', 'w')
f.write(network.to_json())
f.close()
network.save('network.h5')