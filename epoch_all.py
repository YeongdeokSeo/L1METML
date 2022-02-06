import os
import numpy as np
import matplotlib.pyplot as plt
import math


loss_file = open("loss_history.log", 'r')

table = loss_file.readline()
table_split = table.split(",")


print("###############\n")

print("Select variable\n")


loss_file.close()
for i, var in enumerate(table_split):
    loss_file = open("loss_history.log", 'r')
    tmp_line = loss_file.readline()
    print("{}\t {}".format(i, var))

    if '\n' in var:
        table_split[i] = table_split[i].replace('\n', '')


    num_var = i 

    print("\n###############\n")


    print("Plot {} vs epoch curve".format(table_split[num_var]))

    epoch_ = 0
    array_epoch = []
    array_var = []

    while True:
        line = loss_file.readline()
        if not line:
            break

        line_split = line.split(",")
        temp_var = line_split[num_var]

        array_epoch.append(epoch_)
        array_var.append(temp_var)

        epoch_ += 1

    array_var = list(map(float, array_var))


    print(array_var)
    plt.plot(array_epoch, array_var)
    plt.title(table_split[num_var])
    plt.xlabel("epoch")
    plt.ylabel(table_split[num_var])
    # plt.ylim(0,5000)
    # plt.xlim(0,140)
    plt.grid()

    try:
        if not os.path.exists("loss_plot"):
            os.makedirs("loss_plot")
    except OSError:
        print("Error: Creating directory. loss_plot")

    plt.savefig("loss_plot/{}.png".format(table_split[num_var]))
    plt.close("all")
    loss_file.close()

