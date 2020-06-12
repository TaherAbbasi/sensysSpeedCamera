"""
There we initialize the database, insert, delete, and modify data in the
database
"""
import mysql.connector
import os
from mysql.connector import Error
import info_processor
import threading
import footer_adder
import cv2
from os.path import splitext
import char_map
import time
from dataSender import dataSender
import shutil
from shutil import copy2

class DB_Handler(object):
    def __init__(self, config):
        # base_path = path.dirname(__file__)
        # config_path = path.abspath(path.join(base_path, "..", "configs",
        #                                      "config.ini"))
        # self.config = SafeConfigParser()
        self.config = config
        # self.config.read(config_path)
        try:
            self.redlight_db = mysql.connector.connect(
                host=self.config.get("database", "host"),
                user=self.config.get("database", "user"),
                passwd=self.config.get("database", "passwd"),
                database=self.config.get("database", "db_name")
            )
            self.redlight_cursur = self.redlight_db.cursor()
        except Error as e:
            print(e)
            print("Error in crating database ")

    def initialize_db(self):
        cursor = redlight_db.cursor()
        redlight_cursur.execute(
            "CREATE DATABASE IF NOT EXISTS %s" % self.config.get(
                "database", "db_name")
        )
        redlight_cursur.close()
        redlight_db.close()

        redlight_db = mysql.connector.connect(
            host=self.config.get("database", "host"),
            user=self.config.get("database", "user"),
            passwd=self.config.get("database", "passwd"),
            database=self.config.get("database", "db_name")
        )
        redlight_cursur = redlight_db.cursor()
        redlight_cursur.execute(
            "ALTER DATABASE `%s` CHARACTER SET 'utf8' COLLATE 'utf8_general_ci'\
            " % self.config.get("database", "db_name"))

        redlight_cursur.execute(
            """
            CREATE TABLE IF NOT EXISTS cameras (
                name_fa VARCHAR(50),
                police_code INT,
                deviceId INT,
                name_en VARCHAR(50) PRIMARY KEY
            )
            """
        )
        self.redlight_db.commit()

        redlight_cursur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                username VARCHAR(255) UNIQUE KEY,
                password VARCHAR(255)
            )
            """
        )
        self.redlight_db.commit()

        redlight_cursur.execute(
            """
            CREATE TABLE IF NOT EXISTS violation_types (
                name_en ENUM('CONFIRMED','STOPPED', 'FALSE_START', 'INVALID') UNIQUE KEY,
                name_fa VARCHAR(255),
                code INT UNIQUE KEY
            )
            """
        )
        self.redlight_db.commit()

        try:
            redlight_cursur.execute(
                """
                CREATE TABLE IF NOT EXISTS violations
                (
                    id INT AUTO_INCREMENT UNIQUE KEY,
                    dir_path VARCHAR(255) ,
                    state ENUM('dir_inserted', \
                               'info_inserted', \
                               'sent', \
                               'NotSent', \
                               'second_ocr_done', \
                               'second_ocr_failed', \
                               'footer_added', \
                               'rejected', \
                               'archived', \
                               'under_process', \
                               'not_processed') NOT NULL,
                    second_ocr CHAR(12),
                    PLATE CHAR(12),
                    second_ocr_confidence FLOAT,
                    OCRSCORE INT,
                    violation_type ENUM('CONFIRMED','STOPPED', 'FALSE_START', 'INVALID'),
                    gray_image VARCHAR(255),
                    gray_image_2 VARCHAR(255),
                    plate_image VARCHAR(255),
                    plate_roi VARCHAR (50),
                    plate_roi_2 VARCHAR (50),
                    footer_image VARCHAR(255),
                    footer_image_gray VARCHAR(255),
                    camera_name_en VARCHAR(255),
                    TR_DATE DATE,
                    TR_TIME TIME,
                    IMAGENAME VARCHAR(255),
                    response_code INT,
                    token VARCHAR(255),
                    operator_name VARCHAR(255),
                    violation_code INT,
                    ocr_edited BOOLEAN,
                    gray_image2 VARCHAR(255),
                    color_image2 VARCHAR(255),
                    merged_image VARCHAR(255),
                    RED_TIME_MS INT,
                    pk VARCHAR(400) PRIMARY KEY,
                    FOREIGN KEY (camera_name_en) REFERENCES cameras(name_en) ON DELETE CASCADE,
                    FOREIGN KEY (operator_name) REFERENCES users(username) ON DELETE CASCADE,
                    FOREIGN KEY (violation_type) REFERENCES violation_types(name_en) ON DELETE CASCADE
                )
                """
            )
        except TypeError as e:
            print(e)
        self.redlight_db.commit()

    def insert_dir(self, violation_info):
        sql_command = "INSERT IGNORE INTO violations (DIR_PATH, camera_name_en, pk) VALUES \
                        (%s, %s, %s)"
        # try:
        print('Violations to be inserted: ', len(violation_info))
        try:
            self.redlight_cursur.executemany(sql_command, violation_info)
            self.redlight_db.commit()
        except Exception as e:
            print(e)       
        # try:
        #     self.redlight_cursur.execute(sql_command, (violation_info['dir_path'], violation_info['camera_name_en'], violation_info['dir_path'], violation_info['camera_name_en']))
        #     self.redlight_db.commit()
        # except Exception as e:
        #     print(e)
    def insert_camera(self, camera_info):
        cursur = self.redlight_cursur
        # print("camera added")
        sql_command = "INSERT INTO cameras (name_fa, police_code, deviceId, name_en) VALUES \
                        (%s, %s, %s, %s)"
        try:
            cursur.execute(sql_command, (camera_info["name_fa"],
                                        camera_info["police_code"],
                                        camera_info["deviceId"],
                                        camera_info["name_en"]))
            
            self.redlight_db.commit()
        except Exception:
            print("Insert Camera Exception")

    def insert_user(self, user_info):
        cursur = self.redlight_cursur
        # print("user added")
        sql_command = "INSERT INTO users (username, password) VALUES \
                        (%s, %s)"
        try:
            cursur.execute(sql_command, (user_info["username"],
                                         user_info["password"]))
            self.redlight_db.commit()
        except Exception:
            print("Insert User Exception")

    def insert_violation(self, violation_info):
        cursur = self.redlight_cursur
        sql_command = "INSERT INTO violation_types (name_en, name_fa, code) VALUES \
                        (%s, %s, %s)"
        try:
            cursur.execute(sql_command, (violation_info["name_en"],
                                         violation_info["name_fa"],
                                         violation_info["code"]))
            self.redlight_db.commit()
        except Exception:
            print("Insert Violation Exception")

    def insert_csv_info(self):
        sql_command_get = "SELECT violations.id, \
                            violations.dir_path, \
                            violations.violation_type, \
                            cameras.police_code \
                            FROM violations INNER JOIN cameras \
                            ON violations.camera_name_en = cameras.name_en \
                            WHERE state = 'dir_inserted'"

        sql_command_get_filtered = "SELECT violations.id, \
                                    violations.PLATE, \
                                    violations.TR_DATE, \
                                    violations.TR_TIME, \
                                    cameras.police_code \
                                    FROM violations INNER JOIN cameras \
                                    ON violations.camera_name_en = cameras.name_en \
                                    WHERE state = 'info_inseted' \
                                    or state = 'sent' \
                                    or state='footer_added' "

        sql_command_update = "UPDATE violations SET state = %s, gray_image = %s, gray_image2 = %s, \
                                violation_type = %s, TR_DATE = %s, TR_TIME = %s, PLATE = %s, \
                                OCRSCORE = %s, \
                                RED_TIME_MS = %s, IMAGENAME = %s, color_image2 = %s, \
                                merged_image = %s, plate_roi = %s, plate_roi_2 = %s, \
                                plate_image = %s  WHERE id = %s"      

        sql_command_not_processed = "UPDATE violations SET state = 'not_processed' WHERE id = %s"     

        while True:
            redlight_db = mysql.connector.connect(
                host=self.config.get("database", "host"),
                user=self.config.get("database", "user"),
                passwd=self.config.get("database", "passwd"),
                database=self.config.get("database", "db_name"))
            cursur = redlight_db.cursor()
            cursur.execute(sql_command_get_filtered)
            violations_filtered = cursur.fetchall()
            violation_infos_filtered = []
            for v in violations_filtered:
                vd = {}
                vd['PLATE'] = v[0]
                vd['DATE'] = v[1]
                vd['TIME'] = v[2]
                vd['police_code'] = v[3]
                violation_infos_filtered.append(vd)

            cursur.execute(sql_command_get)
            violations = cursur.fetchall()
            violation_infos = []
            print(f'Violation info list: {len(violations)}')

            for v in violations:
                id = v[0]
                dir_path = v[1]
                violation_type = v[2]
                police_code = v[3]
                try:
                    file_names = os.listdir(dir_path)
                except:
                    print('Files Not Listed')
                    # cursur.execute(sql_command_not_processed, (id,))
                    # redlight_db.commit()
                    continue
                color_image2 = ""
                IMAGENAME = ""
                gray_image = ""
                gray_image2 = ""
                merged_image_path = ""

                for f in file_names:
                    if f.endswith('IRN_CTX_1.jpg'):
                        IMAGENAME = os.path.join(dir_path, f)
                    elif f.endswith('IRN_CTX_2.jpg'):
                        color_image2 = os.path.join(dir_path, f)
                    elif f.endswith('.csv'):
                        try:
                            os.remove(f)
                        except Exception as e:
                            print('couldnt remove csv', e)
                    elif f.endswith('IRN.jpg'):
                        if gray_image:
                            gray_image2 = os.path.join(dir_path, f)
                        else:
                            gray_image = os.path.join(dir_path, f)

                merged_image_path = info_processor.merge(IMAGENAME, color_image2)
                try:
                    violation_info_csv = info_processor.get_image_attributes(gray_image, gray_image2)
                except Exception as e:
                    print(e)
                    # cursur.execute(sql_command_not_processed, (id,))
                    # redlight_db.commit()
                    continue
                if violation_info_csv:
                    violation_info_csv['police_code'] = police_code
                if violation_info_csv:
                    try:
                        same_list = info_processor.is_listed(violation_info_csv, violation_infos+violation_infos_filtered)
                        if not same_list:
                            cursur.execute(sql_command_update,('info_inserted',
                                                violation_info_csv['gray_image'],
                                                violation_info_csv['gray_image2'],
                                                violation_info_csv['violation_type'],
                                                violation_info_csv['DATE'],
                                                violation_info_csv['TIME'],
                                                violation_info_csv['PLATE'],
                                                violation_info_csv['OCRSCORE'],
                                                violation_info_csv['RED_TIME_MS'],
                                                IMAGENAME,
                                                color_image2,
                                                merged_image_path,
                                                violation_info_csv['plate_roi'],
                                                violation_info_csv['plate_roi_2'],
                                                violation_info_csv['plate_image'],
                                                id))
                            redlight_db.commit()
                            violation_infos.append(violation_info_csv)
                        else:
                            cursur.execute(sql_command_not_processed, (id,))
                            redlight_db.commit()
                            # print(f"{violation_info_csv['DATE']} {violation_info_csv['TIME']}: {violation_info_csv['PLATE']} {violation_info_csv['police_code']}")
                            # print(f"{same_list[0]['DATE']} {same_list[0]['TIME']}: {same_list[0]['PLATE']} {same_list[0]['police_code']}")
                            # print('#################')
                    except Exception as e:
                        print(violation_info_csv)
                        print(e)
                else:
                    pass
                    # print('NOT_PROCESSED: ', dir_path)
                    # cursur.execute(sql_command_not_processed, (id,))
                    # redlight_db.commit()
            cursur.close()
            redlight_db.close()
            time.sleep(100)

    def get_complete_violations(self):
        # print("db_handler: get_complete_violation:")

        TTCC_dataSender = dataSender()
        sql_command_get_footerAdded = "SELECT \
                        violations.id, \
                        violations.footer_image, \
                        violations.footer_image_gray, \
                        violations.TR_DATE, \
                        violations.TR_TIME, \
                        cameras.deviceId, \
                        violations.PLATE, \
                        violation_types.code, \
                        cameras.police_code, \
                        cameras.name_fa, \
                        violations.gray_image, \
                        violations.plate_image, \
                        violations.camera_name_en \
                        FROM violations \
                        INNER JOIN cameras \
                        ON violations.camera_name_en = cameras.name_en \
                        INNER JOIN violation_types \
                        ON violations.violation_type = violation_types.name_en \
                        WHERE violations.state = 'footer_added' and \
                        violations.TR_DATE > '2020-05-05' ORDER BY TR_DATE DESC, TR_TIME"
        while True:
            redlight_db = mysql.connector.connect(
                host=self.config.get("database", "host"),
                user=self.config.get("database", "user"),
                passwd=self.config.get("database", "passwd"),
                database=self.config.get("database", "db_name")
            )
            cursur = redlight_db.cursor()
            cursur.execute(sql_command_get_footerAdded)
            violations = cursur.fetchall()
            viol_info = dict()
            print("Length of Sent List: ", len(violations))
            for v in violations:
                viol_info['id'] = v[0]
                viol_info['footer_image_path'] = v[1]

                is_large = False
                viol_info['footer_image_path'], is_large = info_processor.image_size_limiter(viol_info['footer_image_path'])
                if is_large:
                    continue

                viol_info['footer_image_gray_path'] = v[2]

                is_large = False
                viol_info['footer_image_gray_path'], is_large = info_processor.image_size_limiter(viol_info['footer_image_gray_path'])
                if is_large:
                    continue

                viol_info['TR_DATE'] = v[3]
                viol_info['TR_TIME'] = v[4]
                viol_info['deviceId'] = v[5]
                viol_info['PLATE'] = v[6]
                viol_info['CrimeCode'] = v[7]
                viol_info['police_code'] = v[8]
                viol_info['location'] = v[9].encode("utf-8").decode("utf-8")
                viol_info['image_gray'] = v[10]
                viol_info['plate_image'] = v[11]
                viol_info['camera_name_en'] = v[12]

                sql_command = "UPDATE violations \
                                    SET state = %s \
                                    WHERE id = %s"
                cursur.execute(sql_command, ('under_process', viol_info['id']))
                redlight_db.commit()
                try:
                    response_code, token = TTCC_dataSender.send(viol_info)
                    if response_code == 201:
                        state = 'sent'
                    elif response_code == 0:
                        state = 'NotSent'
                    else:
                        state = 'rejected'
                except:
                    state = 'NotSent'
                print(f"{viol_info['TR_DATE']} {viol_info['TR_TIME']} {state} {viol_info['PLATE']} {viol_info['camera_name_en']}")

                sql_command = "UPDATE violations \
                                    SET response_code = %s, \
                                    token = %s, \
                                    state = %s \
                                    WHERE id = %s"
                cursur.execute(sql_command, (response_code, token, state, viol_info['id']))
                redlight_db.commit()
                # time.sleep(1)
            cursur.close()
            redlight_db.close()
            time.sleep(100)

    def datis_ocr(self, plate_reader):

        while True:
            redlight_db = mysql.connector.connect(
                host=self.config.get("database", "host"),
                user=self.config.get("database", "user"),
                passwd=self.config.get("database", "passwd"),
                database=self.config.get("database", "db_name")
            )
            cursor = redlight_db.cursor()
            sql_command = "SELECT \
                        id, \
                        gray_image, \
                        PLATE \
                        FROM violations WHERE state = 'info_inserted' and camera_name_en LIKE '%zanjan_golha%'"
            cursor.execute(sql_command)
            violations = cursor.fetchall()
            print("Info Inserted: ", len(violations))
            for v in violations:
                id = v[0]
                image_path = v[1]
                camera_ocr = v[2]
                plate = plate_reader.get_plate(image_path, camera_ocr)
                if not plate:
                    plate = {}
                    state = "second_ocr_failed"
                    plate['ocr'] = "00000000"
                    plate_path = ""
                    state = "second_ocr_failed"
                    plate['confidence'] = 0
                    plate_roi = ""
                else:
                    state = "second_ocr_done"
                    plate_path = "{0}_{2}{1}".format(*splitext(image_path) + ("plate",))
                    cv2.imwrite(plate_path, plate['image'])
                    plate_roi = str(plate['roi'])
                sql_command = "UPDATE violations \
                            SET state = %s, \
                            second_ocr = %s, \
                            plate_image = %s, \
                            second_ocr_confidence = %s, \
                            plate_roi = %s \
                            WHERE id = %s"
                cursor.execute(sql_command, (state,
                            plate['ocr'],
                            plate_path,
                            plate['confidence'],
                            plate_roi,
                            id))
                redlight_db.commit()
            cursor.close()
            redlight_db.close()
            time.sleep(100)

    def get_users(self):
        redlight_db = mysql.connector.connect(
            host=self.config.get("database", "host"),
            user=self.config.get("database", "user"),
            passwd=self.config.get("database", "passwd"),
            database=self.config.get("database", "db_name")
        )
        cursur = redlight_db.cursor()
        sql_command = "SELECT \
                       username, \
                       password \
                       FROM users"

        # print(sql_command)
        cursur.execute(sql_command)
        users_info = cursur.fetchall()
        users = []
        for user_info in users_info:
            username = user_info[0]
            password = user_info[1]
            user = dict()
            user['username'] = username
            user['password'] = password
            users.append(user)
        return users

    def get_violations_info(self, operator_name, violation_state,
                            no_of_violations, second_ocr_confidence_limit):
        redlight_db = mysql.connector.connect(
            host=self.config.get("database", "host"),
            user=self.config.get("database", "user"),
            passwd=self.config.get("database", "passwd"),
            database=self.config.get("database", "db_name")
        )
        cursur = redlight_db.cursor()
        sql_command = "UPDATE violations SET \
                       state = 'under_process', \
                       operator_name = %s \
                       WHERE state=%s \
                       LIMIT %s"
        cursur.execute(sql_command, (
                       operator_name,
                       violation_state,
                       no_of_violations))
        redlight_db.commit()
        sql_command = "SELECT \
                       violations.id, \
                       violations.footer_image_gray, \
                       violations.gray_image, \
                       violations.TR_DATE, \
                       violations.TR_TIME, \
                       violations.RED_TIME_MS, \
                       violation_types.name_fa, \
                       cameras.name_fa, \
                       violations.PLATE, \
                       violations.second_ocr, \
                       violations.second_ocr_confidence, \
                       violations.OCRSCORE, \
                       violations.plate_image \
                       FROM violations \
                       INNER JOIN cameras \
                       ON violations.camer_name_en = cameras.name_en \
                       INNER JOIN violation_types \
                       ON violation_types.name_en = violations.violation_type \
                       WHERE (violations.state ='under_process' \
                       AND violations.operator_name = %s)"
        # try:
        cursur.execute(sql_command, (operator_name, ))
        # except Exception:
        #     print(Exception)
        violations = cursur.fetchall()
        violations_info = []
        info = {}
        for v in violations:
            info = {}
            info['id'] = v[0]
            info['footer_image_gray'] = v[1]
            info['gray_image'] = v[2]
            info['TR_DATE'] = v[3]
            info['TR_TIME'] = v[4]
            info['RED_TIME_MS'] = v[5]
            info['violation_name'] = v[6].encode("utf-8").decode("utf-8")
            info['location'] = v[7].encode("utf-8").decode("utf-8")
            second_ocr_confidence = v[10]
            if second_ocr_confidence < second_ocr_confidence_limit:
                info['ocr'] = v[8]
                info['confidence'] = v[11]
            else:
                info['ocr'] = v[9]
                info['confidence'] = v[10]
            info['plate_image'] = v[12]
            violations_info.append(info)
        return violations_info

    def update_violation(self, violation_info):
        redlight_db = mysql.connector.connect(
            host=self.config.get("database", "host"),
            user=self.config.get("database", "user"),
            passwd=self.config.get("database", "passwd"),
            database=self.config.get("database", "db_name")
        )
        cursur = redlight_db.cursor()
        sql_command = "UPDATE violations SET \
                       state = %s, \
                       operator_name = %s, \
                       second_ocr = %s, \
                       plate_image = %s \
                       WHERE id= %s"
        cursur.execute(sql_command, (
                       violation_info['state'],
                       violation_info['operator_name'],
                       violation_info['second_ocr'],
                       violation_info['plate_image'],
                       violation_info['id']))
        redlight_db.commit()

    def footer_images(self):
        while True:
            redlight_db = mysql.connector.connect(
                host=self.config.get("database", "host"),
                user=self.config.get("database", "user"),
                passwd=self.config.get("database", "passwd"),
                database=self.config.get("database", "db_name")
            )
            cursor = redlight_db.cursor()
            sql_command = "SELECT \
                        violations.id, \
                        violations.gray_image, \
                        violations.IMAGENAME, \
                        violations.TR_DATE, \
                        violations.TR_TIME, \
                        violations.RED_TIME_MS, \
                        violation_types.name_fa, \
                        cameras.police_code, \
                        cameras.name_fa, \
                        violations.merged_image, \
                        violations.violation_type, \
                        violations.plate_roi, \
                        violations.camera_name_en, \
                        violations.plate_roi_2 \
                        FROM violations \
                        INNER JOIN cameras \
                        ON violations.camera_name_en = cameras.name_en \
                        INNER JOIN violation_types \
                        ON violations.violation_type = violation_types.name_en \
                        WHERE violations.state ='info_inserted' ORDER BY TR_DATE DESC, TR_TIME"

            cursor.execute(sql_command)
            violations = cursor.fetchall()
            footer_info = dict()
            print("Length of FooterAdder list: ", len(violations))
            for v in violations:
                footer_info['id'] = v[0]
                footer_info['image_path'] = v[1]
                footer_info['TR_DATE'] = v[3]
                footer_info['TR_TIME'] = v[4]
                footer_info['RED_TIME_MS'] = v[5]
                footer_info['violation_type'] = v[6]
                footer_info['police_code'] = v[7]
                footer_info['location'] = v[8].encode("utf-8").decode("utf-8")
                footer_image_gray_path = None
                footer_image_path = None
                footer_image_gray_path = footer_adder.add(footer_info, "gray")
                footer_info['violation_type_en'] = v[10]
                footer_info['plate_roi'] = v[11]
                footer_info['camera_name_en'] = v[12]
                footer_info['plate_roi_2'] = v[13]
                if footer_info['violation_type_en'] == "STOPPED":
                    footer_info['image_path'] = v[2]
                    footer_image_path = footer_adder.add(footer_info, "color")
                elif footer_info['violation_type_en'] == "CONFIRMED":
                    footer_info['image_path'] = v[9]
                    footer_image_path = footer_adder.add(footer_info, "color")

                if footer_image_gray_path =='footer_not_added' or footer_image_path =='footer_not_added':
                    print(f"Matrice not exists: {footer_info['camera_name_en']}")
                    continue
                if footer_image_gray_path and footer_image_path:
                    # print(f"{footer_info['TR_DATE']} {footer_info['TR_TIME']} footer_added {footer_info['camera_name_en']}")
                    sql_command = "UPDATE violations SET state = %s, footer_image = %s, \
                                footer_image_gray = %s WHERE id = %s"
                    cursor.execute(sql_command, ("footer_added",
                                    footer_image_path,
                                    footer_image_gray_path,
                                    footer_info['id']))
                else:
                    sql_command = "UPDATE violations SET state = %s WHERE id = %s"
                    cursor.execute(sql_command, ("not_processed", footer_info['id']))                
                redlight_db.commit()
            cursor.close()
            redlight_db.close()
            time.sleep(100)

    def move_sent(self, from_dir='ftp', to_dir='sent'):
        redlight_db = mysql.connector.connect(
            host=self.config.get("database", "host"),
            user=self.config.get("database", "user"),
            passwd=self.config.get("database", "passwd"),
            database=self.config.get("database", "db_name")
        )
        cursur = redlight_db.cursor()
        sql_command = "SELECT \
                    id, \
                    dir_path FROM violations \
                    WHERE state IN ('sent', 'archived', 'rejected') or tr_date < '2020-04-15' or response_code=490 or violation_type = 'FALSE_START' or (camera_name_en like '%abshenasan_shahran%' and state='not_processed')"

        cursur.execute(sql_command)
        sent_violations = cursur.fetchall()
        archived_list = []
        for v in sent_violations:
            id = v[0]
            from_dir_path = v[1]
            to_dir_path = from_dir_path.replace(from_dir, to_dir)

            try:
                shutil.move(from_dir_path, to_dir_path, copy_function=copy2)
                # print('archived: ', from_dir_path)
            except Exception as e:
                pass
            archived_list.append(('archived', id))
            try:
                os.rmdir(from_dir_path)
            except Exception as e:
                pass
        sql_command = "UPDATE violations SET \
                state = %s \
                WHERE id = %s"
        cursur.executemany(sql_command, archived_list)
        redlight_db.commit()
        cursur.close()
        redlight_db.close()

def camera_report(self):
    pass
