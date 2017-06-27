# coding=utf-8
import sqlite3
import datetime
import os
import subprocess
import calendar


def getTimestamp(mode):  # returns timestamp in array format
    if mode == "split":
        return str('"%s"' % datetime.datetime.now()).split()[0].replace('"', '').split('-')
    else:
        return str('"%s"' % datetime.datetime.now())


def dbConnect():  # connects to the database
    filepath = os.getcwd() + '/yeti/sqlite3.db'
    conn = sqlite3.connect(filepath)
    return conn


def dbInsert(c, file_list):  # inserts the contents of the files into the database, starting from the last id number
    for file in file_list:
        c.execute(
            'SELECT * FROM taxii_services_contentblock WHERE id = (SELECT MAX(id) FROM taxii_services_contentblock)')
        tuple = c.fetchone()
        try:
            id = tuple[0] + 1
        except:
            id = 1
        try:
            c.execute("INSERT INTO taxii_services_contentblock VALUES(%s,'',%s,null,3,'%s','',%s,%s)" % (
                id, getTimestamp('not'), file[1], getTimestamp('not'), getTimestamp('not')))
            c.execute("INSERT INTO taxii_services_datacollection_content_blocks VALUES(%s, 1, %s)" % (id, id))
            print "Wrote '%s' to the database." % file[0]
        except:
            print "fail"

def datafeedClear(c):
    c.execute('DELETE FROM taxii_services_datacollection_content_blocks')


def dbDisconnect(conn):  # commit changes and dc from database
    conn.commit()
    conn.close()


def getFileInfo():  # get contents of ioc files
    filepath = os.getcwd()
    filepath = filepath + '/iocs/'
    file_list = []

    for file in os.listdir(filepath):
        if file.endswith(".xml"):
            f = open(filepath + file)
            filename = f.name.split('/')[-1]
            filecontent = f.read().replace("'", "")
            file_list.append((filename, filecontent))
            os.rename(f.name, f.name.replace('/iocs', '/iocs/archive'))
            f.close()

    return file_list


def populate():  # connect to database, insert file contents in data blocks and disconnect from database
    conn = dbConnect()
    c = conn.cursor()
    datafeedClear(c)
    file_list = getFileInfo()
    dbInsert(c, file_list)
    dbDisconnect(conn)


def getMonthDaycount(m):
    if m == 1 or m == 3 or m == 5 or m == 7 or m == 8 or m == 10 or m == 12:
        return 31
    else:
        return 30


def init_poll():
    y = 2017
    filepath = os.getcwd()
    collections = open(filepath + '/collections').read().split()

    for collection in collections:
        for m in range(1, 6):
            day = getMonthDaycount(m)
            for d in range(1, day + 1):
                if (day == 30 and d == 30) or (day == 31 and d == 31):
                    subprocess.call(
                        ['poll_client', '--host', 'hailataxii.com', '--username', 'guest', '--pass', 'guest',
                         '--path', '/taxii-data', '--collection', '%s' % (collection), '--begin-timestamp',
                         '%d-%d-%dT00:00:00.000000+0:00' % (y, m, d), '--end-timestamp',
                         '%d-%d-%dT00:00:00.000000+0:00' % (y, m + 1, 1), '--dest-dir',
                         '/home/crisbarbosa/Documents/STIX_results'])
                else:
                    subprocess.call(
                        ['poll_client', '--host', 'hailataxii.com', '--username', 'guest', '--pass', 'guest', '--path',
                         '/taxii-data', '--collection', '%s' % (collection), '--begin-timestamp',
                         '%d-%d-%dT00:00:00.000000+0:00' % (y, m, d), '--end-timestamp',
                         '%d-%d-%dT00:00:00.000000+0:00' % (y, m, d + 1), '--dest-dir',
                         '/home/crisbarbosa/Documents/STIX_results'])


def getWeek(year, month, day):
    if month < 10:
        today = [str(year), '0' + str(month), str(day)]
    else:
        today = [str(year), str(month), str(day)]

    cal = calendar.Calendar(5)
    m = []

    for d in cal.itermonthdates(year, month):
        d = str(d).split('-')
        m.append(d)

    i = m.index(today)
    week = []

    for index in range(len(m) - 1):
        if index <= i and index > i - 7:
            week.append(m[index])

    return week


def weeklyPoll():
    filepath = os.getcwd()
    day = getTimestamp("split")
    year = int(day[0])
    month = int(day[1])
    day = int(day[2])

    week = getWeek(year, month, day)

    for index in range(len(week) - 1):
        subprocess.call(
            ['poll_client', '--host', 'hailataxii.com', '--username', 'guest', '--pass', 'guest', '--path',
             '/taxii-data', '--collection', 'guest.dataForLast_7daysOnly', '--begin-timestamp',
             '%s-%s-%sT00:00:00.000000+0:00' % (week[index][0], week[index][1], week[index][2]), '--end-timestamp',
             '%s-%s-%sT00:00:00.000000+0:00' % (week[index+1][0], week[index+1][1], week[index+1][2]), '--dest-dir',
             '%s/iocs' % filepath])

def dailyPoll():
    filepath = os.getcwd()
    day = getTimestamp("split")
    year = int(day[0])
    month = int(day[1])
    day = int(day[2])

    week = getWeek(year, month, day)

    subprocess.call(
        ['poll_client', '--host', 'hailataxii.com', '--username', 'guest', '--pass', 'guest', '--path',
         '/taxii-data', '--collection', 'guest.dataForLast_7daysOnly', '--begin-timestamp',
         '%s-%s-%sT00:00:00.000000+0:00' % (week[5][0], week[5][1], week[5][2]), '--end-timestamp',
         '%s-%s-%sT00:00:00.000000+0:00' % (week[6][0], week[6][1], week[6][2]), '--dest-dir',
         '%s/iocs' % filepath])


if __name__ == '__main__':
    #dailyPoll()
    populate()