# pylint: disable=C0301
# pylint: disable=E0401
# pylint: disable=C0114
# pylint: disable=C0412
# pylint: disable=R1723
# pylint: disable=C0103
# Copyright 2021 - 2022, Alvin Kuruvilla <alvineasokuruvilla@gmail.com>, Dr. Rajesh Kumar <Rajesh.Kumar@hofstra.edu>

# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import os
import sys
from dotenv import load_dotenv
from base.backends.sql import SQLDriver, check_mysql_installed
from base.backends.yaml_driver import get_all_associated_values, print_as_table
from base.user_ops.sql_ops import add_user_to_db, display_profile_from_db
from base.user_ops.yml_ops import create_user, user_id_to_yaml_file_path
from base.util import clear_screen, banner, block_text, km_prompt
from base.log import Logger
from tools.keylogger import Keylogger
from tools.env_verifier import verify_env_values
from tools.pid_printer import print_pid


class TUI:
    def __init__(self):
        pass

    def run(self):
        log = Logger()
        if not os.path.isdir(os.path.join(os.getcwd(), "logs")):
            os.makedirs(os.path.join(os.getcwd(), "logs"))
        if not os.path.isdir(os.path.join(os.getcwd(), "users")):
            os.makedirs(os.path.join(os.getcwd(), "users"))
        clear_screen()
        print_pid()
        input(km_prompt("Press any key to continue "))
        clear_screen()
        if check_mysql_installed():
            verify_env_values()
            input(km_prompt("Press any key to continue "))
            clear_screen()
        banner("KMLogger")
        load_dotenv()
        print("\nChoose service you want to use : ")
        print(
            """
            1:  Start KMLogger
            2:  Exit
            """
        )
        while True:
            choice = int(input(km_prompt("Enter a choice: ")))
            if choice in (1, 2):
                break
            else:
                log.km_error("Invalid selection: choose 1 or 2")
                continue
        if choice == 1:
            clear_screen()
            block_text("Keylogger")
            if check_mysql_installed():
                driver = SQLDriver()
                driver.try_connect()
            else:
                log.km_info("MySQL not installed, falling back to YAML system")
            user_id = input(km_prompt("Enter your user_id: "))
            # Step through of the reasoning behind the lines below:
            #   - Make the driver query the table for the user_id table
            #   - Fetch and store the result of that call
            #   - Iterate through the results to see if any match the id the user
            #     entered
            #   - If that id is not in the table create a new user, add them to the
            #     table and start the keylogger
            #   - If they are in the table, let them know that, and then start the
            #     keylogger
            if check_mysql_installed():
                # NOTE: To understand this api look in the mysql package's cursor.py
                # file...According to that api the params argument as they have named it
                # defaults to an empty tuple
                cursor = driver.query("SELECT user_id FROM " + os.getenv("TABLE"), ())
                # NOTE: Here it should be okay to use fetchone rather fetchmany or fetchall because we are assuming that each user_id will be unique, so there will only ever be at most 1 row in the result
                result = cursor.fetchone()
                if result is not None and user_id in result:
                    log.km_info("User ID: " + user_id + " found")
                    display_profile_from_db(user_id)
                    info_correct = input(
                        km_prompt("Is all of this information correct? y/n: ")
                    )
                    if info_correct.lower() == "y" or info_correct.lower() == "yes":
                        km = Keylogger(user_id)
                        km.start_recording()
                    elif info_correct.lower() == "n" or info_correct.lower() == "no":
                        log.km_fatal(
                            "Please let the researchers know that this information is incorrect and it will be addressed"
                        )
                    else:
                        log.km_fatal("Invalid Input")
                else:
                    log.km_info("ID not found")
                    km = Keylogger(user_id)
                    add_user_to_db(user_id)
                    km.start_recording()
            else:
                # The yaml version of the above code
                comp = get_all_associated_values("user_id")
                if user_id in comp:
                    log.km_info("User ID: " + user_id + " found")
                    print_as_table(user_id_to_yaml_file_path(user_id))
                    while True:
                        info_correct = str(
                            input(
                                km_prompt("Is all of this information correct? y/n: ")
                            )
                        )
                        if info_correct.lower() == "y" or info_correct.lower() == "yes":
                            km = Keylogger(user_id)
                            km.start_recording()
                            break
                        elif (
                            info_correct.lower() == "n" or info_correct.lower() == "no"
                        ):
                            log.km_fatal(
                                "Please let the researchers know that this information is incorrect and it will be addressed"
                            )
                            break
                        else:
                            log.km_fatal("Invalid Input")
                else:
                    log.km_info("User not found, creating a new user")
                    create_user(user_id)
                    print_as_table(user_id_to_yaml_file_path(user_id))
                    while True:
                        info_correct = str(
                            input(
                                km_prompt("Is all of this information correct? y/n: ")
                            )
                        )
                        if info_correct.lower() == "y" or info_correct.lower() == "yes":
                            km = Keylogger(user_id)
                            km.start_recording()
                            break
                        elif (
                            info_correct.lower() == "n" or info_correct.lower() == "no"
                        ):
                            log.km_fatal(
                                "Please let the researchers know that this information is incorrect and it will be addressed"
                            )
                            break
                        else:
                            log.km_fatal("Invalid Input")

        if choice == 2:
            log.km_info("Exiting KMLogger")
            sys.exit(0)


if __name__ == "__main__":
    tui = TUI()
    tui.run()
