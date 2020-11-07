from genderize import Genderize, GenderizeException
import csv
import sys
import os.path
import time
import argparse
import logging

import jpyhelper as jpyh

# Allow override command line input                                                                                 FINISHED
# Allow user input override search column through command line                                                      FINISHED
# Create override column searching                                                                                  FINISHED
# Strip leading and tailing whitespaces from overriden values                                                       FINISHED
# Allow different headers to be written based off of if we are overriding                                           FINISHED
# Print the original file columns if we are overriding                                                              FINISHED
# Allow -a to work with overrides                                                                                   FINISHED    


# TEST CASES:
# No Override, No -a        Tested on file "test_big.csv"                                                           SUCCESS - 300 Names and gender info written
# No Override, Yes -a       Tested on file "test_big.csv"                                                           SUCCESS - 149 Names and gender info written    
# Yes Override, No -a       Tested on file "genderize_test_file.csv"                                                SUCCESS - 51 Names, original information, and Gender info written
# Yes Override, Yes -a      Tested on file "genderize_test_file.csv"                                                SUCCESS - 45 Names, original information, and Gender info written






#def remove_dupes(list):
#    return list(dict.fromkeys(list))
    
    
def remove_dupes(list, search_column):
    names = []
    removeList = []
    for index, row in enumerate(list):
        stripped = row[search_column].strip()
        if stripped not in names:
            names.append(stripped)
        else:
            removeList.append(index)
    
    # I know there is a better way to do this, but i could not pop items off of the list in the for loop above
    # without losing an item. A second "michael" was showing up in the final csv file. This method allowed me to get 
    # a proper output on the csv file
    
    for index, remove in enumerate(removeList):
        list.pop(remove - index)
    return list

    
def write_headers(writer, original_headers):
    new_headers = ["gender", "probability", "count"]
    # Add the new headers on the tail end of our original headers list.
    original_headers = original_headers + new_headers
    # Write the original headers list to the output csv file
    writer.writerow(original_headers)

def genderize(args):
    print(args)

    #File initialization
    dir_path = os.path.dirname(os.path.realpath(__file__))

    logging.basicConfig(filename=dir_path + os.sep + "log.txt", level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s %(name)s %(message)s')
    logger=logging.getLogger(__name__)

    ofilename, ofile_extension = os.path.splitext(args.output)

    ofile = ofilename + "_" + time.strftime("%Y%m%d-%H%M%S") + ".csv"
    ifile = args.input

    if os.path.isabs(ifile):
        print("\n--- Input file: " + ifile)
    else:
        print("\n--- Input file: " + dir_path + os.sep + ifile)

    if os.path.isabs(ofile):
        print("--- Output file: " + ofile)
    else:
        print("--- Output file: " + dir_path + os.sep + ofile + "\n")

    #File integrity checking
    if not os.path.exists(ifile):
        print("--- Input file does not exist. Exiting.\n")
        sys.exit()

    if not os.path.exists(os.path.dirname(ofile)):
        print("--- Error! Invalid output file path. Exiting.\n")
        sys.exit()

    #Some set up stuff
    ##csv.field_size_limit(sys.maxsize)

    #Initialize API key
    if not args.key == "NO_API":
        print("--- API key: " + args.key + "\n")
        genderize = Genderize(
            user_agent='GenderizeDocs/0.0',
            api_key=args.key)
        key_present = True
    else:
        print("--- No API key provided.\n")
        key_present = False

    # Modify this section to take into account what the user wants to use through the command line
    #Open ifile
    with open(ifile, 'r', encoding="utf8") as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',', skipinitialspace=True)
        first_name = []
        raw = []
        original_headers = [];
        is_override = False
        column_number = -1
        # we are attempting to override the column that the names are stored in
        
        if args.override != 'NO_OVERRIDE':
            is_override = True
        
        for row in readCSV: #Read CSV into first_name list
            # if we are overriding the search column
            if is_override:
                # ugly nested mess but it works.
                # if we have not found the list position of the desired override column
                if column_number == -1:
                    # get the first row from the reader (assumed to be the first row)
                    first_name.append(row)
                    # also save this to the raw list for later use
                    raw.append(row)
                    # iterate through each item in the row we just saved and keep track of the for loop index
                    for index, column in enumerate(first_name[0]):
                        # if our column name is equal to the override name, we found the index number we need to proceed. Break from the loop
                        if column == args.override:
                            column_number = index
                            break
                # Our column number should be found by now, so continue to import the specific data that we want.
                else:
                    # IMPORTANT: we need to remove all leading and trailing whitespaces to ensure that the genderizer responds with correct information
                    stripped = row[column_number].strip()
                    # append our stripped string onto the first_name list
                    first_name.append(stripped)
                    # save the entire row to the raw list
                    raw.append(row)
                    
                
                    
            # if no override, continue like normal
            else:
                first_name.append(row)
                

        # if we have a header, we need to remove it so it is not included in the submission
        if args.noheader == False:
            if is_override:
                    original_headers = first_name[0]
                    raw.pop(0)
            first_name.pop(0) #Remove header


        o_first_name = list()  
        # We dont need to strip the first name list if we are overriding because it has already been taken care of
        if is_override:
            o_first_name = first_name
        else:
            for l in first_name:
                for b in l:
                    o_first_name.append(b)
                    
        uniq_first_name = []
                    
        if args.auto == True:
            uniq_first_name = list(dict.fromkeys(o_first_name))
            chunks = list(jpyh.splitlist(uniq_first_name, 10));
            print("--- Read CSV with " + str(len(first_name)) + " first_name. " + str(len(uniq_first_name)) + " unique.")
        else:
            # splitting the name list into chunks of 10
            chunks = list(jpyh.splitlist(first_name, 10));
            print("--- Read CSV with " + str(len(first_name)) + " first_name")

        print("--- Processed into " + str(len(chunks)) + " chunks")
        

        if jpyh.query_yes_no("\n---! Ready to send to Genderdize. Proceed?") == False:
            print("Exiting...\n")
            sys.exit()

        if os.path.isfile(ofile):
            if jpyh.query_yes_no("---! Output file exists, overwrite?") == False:
                print("Exiting...\n")
                sys.exit()
            print("\n")

        if args.auto == True:
            ofile = ofile + ".tmp"

        response_time = [];
        gender_responses = list()
        with open(ofile, 'w', newline='', encoding="utf8") as f:
            
            writer = csv.writer(f)
            ## TODO Add new system to write all rows of the original file. Done
            # If we are overriding, we need to do a different process
            if is_override:
                write_headers(writer, original_headers)
            # else, continue as expected
            else:
                writer.writerow(list(["first_name","gender", "probability", "count"]))
            chunks_len = len(chunks)
            stopped = False
            for index, chunk in enumerate(chunks):
                if stopped:
                    break
                success = False
                while not success:
                    try:
                        start = time.time()

                        if key_present:
                            dataset = genderize.get(chunk)
                        else:
                            dataset = Genderize().get(chunk)

                        gender_responses.append(dataset)
                        
                        success = True
                    except GenderizeException as e:
                        #print("\n" + str(e))
                        logger.error(e)

                        #Error handling
                        if "response not in JSON format" in str(e) and args.catch == True:
                            if jpyh.query_yes_no("\n---!! 502 detected, try again?") == True:
                                success = False
                                continue
                        elif "Invalid API key" in str(e) and args.catch == True:
                            print("\n---!! Error, invalid API key! Check log file for details.\n")
                        else:
                            print("\n---!! GenderizeException - You probably exceeded the request limit, please add or purchase a API key. Check log file for details.\n")
                        stopped = True
                        break

                    response_time.append(time.time() - start)
                    print("Processed chunk " + str(index + 1) + " of " + str(chunks_len) + " -- Time remaining (est.): " + \
                        str( round( (sum(response_time) / len(response_time) * (chunks_len - index - 1)), 3)) + "s")
            
            gender_dict = dict()
            
            # Moved this function out of the autocomplete function to allow us to use it for the non-autocomplete
            for response in gender_responses:
                    for d in response:
                        gender_dict[d.get("name")] = [d.get("gender"), d.get("probability"), d.get("count")]

            for index, name in enumerate(o_first_name):
                data = gender_dict.get(name)
                if is_override:
                    data_list = [data[0], data[1], data[2]]
                    writer.writerow(raw[index] + data_list)
                else:
                    writer.writerow([name, data[0], data[1], data[2]])      

            # if we have the autocomplete enabled, we need to allow overriding in this mode as well.

            if args.auto == True:
                print("\nCompleting identical first_name...\n")

                filename, file_extension = os.path.splitext(ofile)
                with open(filename, 'w', newline='', encoding="utf8") as f:
                    writer = csv.writer(f)
                    if is_override:
                        write_headers(writer, original_headers)
                        raw_cleaned = remove_dupes(raw, column_number)
                    else:
                        writer.writerow(list(["first_name","gender", "probability", "count"]))
                    for index, name in enumerate(uniq_first_name):
                        if is_override:
                            data = gender_dict.get(name)
                            data_list = [data[0], data[1], data[2]]
                            writer.writerow(raw_cleaned[index] + data_list)
                        else:
                            data = gender_dict.get(name)
                            writer.writerow([name, data[0], data[1], data[2]])

                    
                    
            print("Done!\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Bulk genderize.io script')
    required = parser.add_argument_group('required arguments')

    required.add_argument('-i','--input', help='Input file name', required=True)
    required.add_argument('-o','--output', help='Output file name', required=True)
    parser.add_argument('-k','--key', help='API key', required=False, default="NO_API")
    parser.add_argument('-c','--catch', help='Try to handle errors gracefully', required=False, action='store_true', default=True)
    parser.add_argument('-a','--auto', help='Automatically complete gender for identical first_name', required=False, action='store_true', default=False)
    parser.add_argument('-nh','--noheader', help='Input has no header row', required=False, action='store_true', default=False)
    parser.add_argument('-ovr','--override',help='override the default search column', required=False, default='NO_OVERRIDE')


    genderize(parser.parse_args())
