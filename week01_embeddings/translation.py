# -*- coding: utf-8 -*-
"""
@Author: andy
@Contact: andy_viky@163.com
@Github: https://github.com/AndyandViky
@Csdn: https://blog.csdn.net/AndyViky
@File: translation.py
@Time: 2020/6/10 下午5:23
@Desc: translation.py
"""
try:
    import torch.nn as nn
    import torch
    import torchtext as tx

    from gensim.models import Word2Vec
    from nltk.tokenize import WordPunctTokenizer
    from torch.nn import LSTM
    from torch import optim

    from config import DATASETS_DIR, DEVICE
    from dataset import get_dataloader

except ImportError as e:
    print(e)
    raise ImportError


'''
model
'''
class Encoder(nn.Module):

    def __init__(self, input_size, hidden_size, num_layers):
        super(Encoder, self).__init__()

        self.model = LSTM(
                input_size=input_size,
                hidden_size=hidden_size,
                num_layers=num_layers,
            )

    def forward(self, x):

        _, state = self.model(x)
        return state


class Decoder(nn.Module):

    def __init__(self, input_size, hidden_size, num_layers):
        super(Decoder, self).__init__()

        self.lstm = LSTM(
                input_size=input_size,
                hidden_size=hidden_size,
                num_layers=num_layers,
            )
        self.linear = nn.Linear(hidden_size, input_size)

    def forward(self, x, states):

        output, _ = self.lstm(x, states)
        output = torch.softmax(self.linear(output), dim=2)
        return output


class Translator(nn.Module):

    def __init__(self, input_size=50, input_decoder_size=50, hidden_size=250, num_layers=5):
        super(Translator, self).__init__()

        self.encoder = Encoder(input_size=input_size, hidden_size=hidden_size, num_layers=num_layers)
        self.decoder = Decoder(input_size=input_decoder_size, hidden_size=hidden_size, num_layers=num_layers)


if __name__ == '__main__':

    # hyper-parameters for Network
    lr = 1e-3
    b1 = 0.5
    b2 = 0.99
    weight_decay = 2.5 * 1e-5
    epoch = 100
    batch_size = 128
    data_name = 'cmn'
    hidden_size = 256
    num_layers = 1

    # get dataloader
    dataloader, input_size, input_decoder_size = get_dataloader(root=DATASETS_DIR, data_name=data_name,
                                                                        batch_size=batch_size)

    # initialization parameters
    translator = Translator(input_size=input_size, input_decoder_size=input_decoder_size,
                            hidden_size=hidden_size, num_layers=num_layers).to(DEVICE)
    xe_loss = nn.CrossEntropyLoss().to(DEVICE)
    optimization = optim.Adam(translator.parameters(), lr=lr, betas=(b1, b2), weight_decay=weight_decay)

    # begin training
    print('translation system ==> data name is: {}, begin training......'.format(data_name))
    for ite in range(epoch):

        total_loss = 0
        for i, (e_input, d_input, d_target) in enumerate(dataloader):

            translator.train()
            translator.zero_grad()
            optimization.zero_grad()

            state = translator.encoder(e_input)
            d_output = translator.decoder(d_input, state)

            loss = xe_loss(d_output, torch.argmax(d_target, dim=1))
            loss.backward()

            optimization.step()

            total_loss += loss.item()
        print('loss: {}'.format(total_loss / len(dataloader)))

