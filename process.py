import datetime
import math
import time
from os.path import join
import os

# Configuration
FXDATA_PATH = "/Users/xuehung/Downloads/FXData2014"
INTERPOLATION_METHOD = "linear"
YEAR = 2014

# Global variables
EPOCH = datetime.datetime(1970,1,1)

def linear_interpolate(y1, y2, mu):
    mu = float(mu)
    return y1 * (1 - mu) + y2 * mu

def cosin_interpolate(y1, y2, mu):
    mu = float(mu)
    mu2 = (1 - math.cos(mu * math.pi)) / 2;
    return y1 * (1 - mu2) + y2 * mu2

def cubic_interpolate(y0, y1, y2, y3, mu):
    mu = float(mu)
    mu2 = mu * mu
    a0 = y3 - y2 - y0 + y1;
    a1 = y0 - y1 - a0;
    a2 = y2 - y0;
    a3 = y1;
    return a0 * mu * mu2 + a1 * mu2 + a2 * mu + a3

def interpolate(method, matrix):
    interpolate_func = None
    # Determine which interpolation method is used
    if method == "linear":
        interpolate_func = linear_interpolate
    elif method == "cosin":
        interpolate_func = cosin_interpolate
    elif method == "cubic":
        interpolate_func = cubic_interpolate
    else:
        raise Exception("Unknown Interpolation Method")

    keys = sorted(matrix.keys())
    klen = len(keys)

    # Interate all timestamps
    for i in range(klen - 1):
        t1 = keys[i]
        t2 = keys[i + 1]
        if t2 - t1 == 1:
            continue
        # Do the interpolation
        for t in range(t1 + 1, t2):
            mu = (t - t1) / float(t2 - t1)
            # Initialize the list
            matrix[t] = [0, 0, 0]
            for j in range(3):
                y1 = matrix[t1][j]
                y2 = matrix[t2][j]
                if method != "cubic":
                    matrix[t][j] = interpolate_func(y1, y2, mu)
                elif i != 0 and i + 2 < klen:
                    y0 = matrix[keys[i - 1]][j]
                    y3 = matrix[keys[i + 2]][j]
                    matrix[t][j] = interpolate_func(y0, y1, y2, y3, mu)
    return


def process_month(input_filepath, matrix):
    with open(input_filepath) as fin:
        for line in fin:
            try:
                # Only use bid
                currency, timestamp, bid, ask = line.strip().split(',')
                bid = float(bid)
                date, time = timestamp.strip().split()
                hour, minute, second = time.split(":")
                minute = datetime.datetime(int(date[0:4]), int(date[4:6]), int(date[6:8]), int(hour), int(minute))
                minute = int((minute - EPOCH).total_seconds() / 60)

                if minute not in matrix:
                    matrix[minute] = [bid, bid, bid]
                else:
                    matrix[minute][0] = max(matrix[minute][0], bid)
                    matrix[minute][1] = min(matrix[minute][1], bid)
                    matrix[minute][2] = bid
            except Exception, e:
                print "Invalid inpute data: %s (%s)" % (line, str(e))
                pass
    return

def process_currency(currency, input_folder_path):
    fx_files = sorted([f for f in os.listdir(input_folder_path) if f.endswith(".csv")])
    output_filepath = join(input_folder_path, "%s_result.csv" % currency)

    # key is time range start
    # element is [max, min, close]
    matrix = {}

    for filename in fx_files:
        matrix = {}
        print "Processing file %s" % filename
        process_month(join(input_folder_path, filename), matrix)
        interpolate(INTERPOLATION_METHOD, matrix)
    return matrix


if __name__ == '__main__':
    #process("../hw2/sample_input.csv", output_filepath)

    currency_list = []
    # For each currency
    folders = [ f for f in os.listdir(FXDATA_PATH)
            if os.path.isdir(join(FXDATA_PATH, f))]

    # The variable to store all data
    matrix_list = []

    for currency in folders:
        print "=== Processing currencies %s" % currency
        matrix = process_currency(currency, join(FXDATA_PATH, currency))
        matrix_list.append(matrix)
        currency_list.append(currency)
        break

    # Output to files
    with open(join(FXDATA_PATH, "%d_result" % YEAR), "w") as fout:
        start_min = int((datetime.datetime(YEAR, 1, 1, 0, 0) - EPOCH).total_seconds() / 60)
        end_min = int((datetime.datetime(YEAR, 12, 31, 23, 59) - EPOCH).total_seconds() / 60)
        fout.write("Time\t")
        for currency in currency_list:
            fout.write("Min(%s)\tMax(%s)\tFinal(%s)\t" % (currency, currency, currency))
        fout.write("\n")
        while start_min <= end_min:
            timestamp = datetime.datetime.utcfromtimestamp(start_min * 60).strftime('%Y-%m-%d %H:%M')
            fout.write("%s\t" % timestamp)
            for i in range(len(currency_list)):
                if start_min in matrix_list[i]:
                    data = matrix_list[i][start_min]
                    fout.write("%f\t%f\t%f\t" % (data[0], data[1], data[2]))
                else:
                    fout.write("N/A\tN/A\tN/A\t")
            fout.write("\n")
            start_min = start_min + 1

