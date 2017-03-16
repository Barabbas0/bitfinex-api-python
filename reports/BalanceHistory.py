import sys
import getopt

def main(argv):
    try:
        opts, args = getopt.getopt(argv,"hl:c:s:")
    except getopt.GetoptError:
        print "BalanceHistory.py -c <USD (or other currency)> -s <since this date> -u <until this date> -l <integer limit of entries to return> -w <wallet. Only acceptable inputs are \"trading\", \"exchange\", and \"deposit\">."
        sys.exit(2)
    if len(opts) < 1:
        print "BalanceHistory.py -c <USD (or other currency)> -s <since this date> -u <until this date> -l <integer limit of entries to return> -w <wallet. Only acceptable inputs are \"trading\", \"exchange\", and \"deposit\">."
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-h" or opt == "":
            print "BalanceHistory.py -c <USD (or other currency)> -s <since this date> -u <until this date> -l <integer limit of entries to return> -w <wallet. Only acceptable inputs are \"trading\", \"exchange\", and \"deposit\">."
            sys.exit(1)
        print "printing arg: " + arg

if __name__ == "__main__":
   main(sys.argv[1:])