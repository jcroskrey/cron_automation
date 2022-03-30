#!/usr/bin/env python
import os
import sys
import time
from crontab import CronTab
import socket
from billing import Environment
import datetime


def main():
    # Determine environment and user.
    hostname = socket.gethostname().split(".")[0]
    host_char = hostname[-1:]

    if host_char == "p":
        env = "PROD"
    elif host_char == "t":
        env = "TEST"
    elif host_char == "i":
        env = "INT"
    elif host_char == "d":
        env = "DEV"
    else:
        # TEST is the default server
        env = "TEST"

    env = Environment(env=env)
    rbmuser = env.servers['rbmuser']

    billopsuser = env.servers['billopsuser']

    print()
    print_text('Billopsuser is: ' + billopsuser)
    print_text('Hit ctrl-c at any point to kill the script and then re-run to start over.')
    print()

    copy_crontab(billopsuser)
    print()

    try:
        setup_job(rbmuser, billopsuser)

    except Exception as e:
        print_text('An error was encountered while trying to configure your job ')
        print_text('(you probably fat-fingered an input).')
        print_text('Reseting and starting over.')
        print()
        setup_job(rbmuser, billopsuser)


def setup_job(rbmuser, billopsuser):
    title_name = get_title_name()
    title = '====== ' + title_name
    print_text('#' + title)
    print()

    directory_name = get_directory_name()
    print_text('Directory is $BIN/' + directory_name)
    print()

    ksh_name = get_ksh_name()
    print_text('ksh script is: ' + ksh_name)
    print()

    cron = CronTab(user=str(rbmuser))
    # cron = CronTab(user='jcroskrey')

    script_to_run = ' /usr/local/rbm/home_dirs/' + billopsuser + '/bin/' + directory_name + '/' + ksh_name
    log_file = ' >> /usr/local/rbm/home_dirs/' + billopsuser + '/log/' + ksh_name[:-4] + '_`hostname`_`date +%Y%m%d`.log 2>&1'

    job = cron.new(
        command=script_to_run + log_file,
        user=str(rbmuser),
        comment=title,
        pre_comment=True,
    )

    entered_time = enter_run_time(job)

    if not entered_time:
        get_run_time(job)

    print()
    print_text('Your cron job is:')
    print_text(job)

    cron.write()
    print()
    print_text('Done! Please double check your job for any typos using "crontab -l".')


def copy_crontab(billopsuser):
    exists = os.path.exists('/usr/local/rbm/home_dirs/' + billopsuser + '/bin/cron_backups')
    if not exists:
        os.mkdir('/usr/local/rbm/home_dirs/' + billopsuser + '/bin/cron_backups')

    todays_date = datetime.date.today().strftime("%Y%m%d")

    copy_exists = os.path.exists('/usr/local/rbm/home_dirs/' + billopsuser + '/bin/cron_backups/crontab.' + todays_date)
    if copy_exists:
        print_text('A copy of crontab from today already exists at:')
        print_text('/usr/local/rbm/home_dirs/' + billopsuser + '/bin/cron_backups/crontab.' + todays_date)
    else:
        os.system('crontab -l > /usr/local/rbm/home_dirs/' + billopsuser + '/bin/cron_backups/crontab.' + todays_date)
        print_text('Copied crontab to /usr/local/rbm/home_dirs/' + billopsuser + '/bin/cron_backups/crontab.' + todays_date)


def get_directory_name():
    print_text('Please enter the $BIN directory that your script exists in (no slashes or path, just the name):')
    directory_name = input()
    check_for_spaces = directory_name.split(' ')
    if len(check_for_spaces) > 1:
        print_text("Please don't include any spaces in the directory name.")
        directory_name = get_directory_name()
    elif len(directory_name) == 0:
        print_text('Directory name cannot be empty.')
        directory_name = get_directory_name()
    elif directory_name[0] == '/':
        directory_name = directory_name[1:]

    return directory_name


def get_title_name():
    print_text("""Enter the title you would like to be at the top of your cron job i.e. #===== <title>:""")
    title_name = input()
    if len(title_name) == 0:
        print_text('Title cannot be empty.')
        title_name = get_title_name()
    return title_name


def get_ksh_name():
    print_text('Enter name of your .ksh file:')
    ksh_name = input().split('.')
    if len(ksh_name) == 0:
        print_text('Name cannot be empty.')
        ksh_name = get_ksh_name()
    elif len(ksh_name) > 2:
        print_text('Name cannot have more than 1 dot in name.')
        ksh_name = get_ksh_name()

    final_name = ksh_name[0] + '.ksh'

    return final_name


def enter_run_time(job):
    print_text("Do you want to enter the cron schedule using cron's syntax?")
    print_text('Or do you want to be walked through it? (cron or walk-through) c|w')
    choice = input().lower()
    if choice == 'c':
        print_text('Enter the schedule in the form (without brackets) <* * * * *>')
        schedule = input().rstrip()
        job.setall(schedule)
        return True

    elif choice == 'w':
        return False


def get_run_time(job):
    print_text("Enter 'restart' at any point to restart the walk-through.")
    while True:
        day_of_week = False
        week_interval = False
        job.every().minute()                                 # If restarted, this line will reset time to * * * * *
        print_text('Will this job run every minute? y|n')
        c = input().lower()
        if c == 'y':
            pass

        elif c == 'n':

            print_text('When called, will this job run at only one minute of the hour? y|n')
            choice = input().lower()

            if choice == 'y':
                print_text('What minute of the hour will it run? 0-59')
                minute_ = input()
                if minute_ == 'restart':
                    print_text('Starting over.')
                    get_run_time(job)
                    break
                minute = int(minute_)
                job.minute.on(minute)

            elif choice == 'n':
                print_text('Will it run on an [i]nterval (every __ days)? Or at [s]pecific minutes? i|s')
                setting = input().lower()

                if setting == 'i':
                    print_text('Every how many minutes do you want this to run? 0-59')
                    num = input()
                    if num == 'restart':
                        print_text('Starting over.')
                        get_run_time(job)
                        break

                    job.minute.every(int(num))

                elif setting == 's':
                    print_text('What minutes do you want it to run at? (comma delimited, no spaces) 1-60')
                    minutes = input().split(',')
                    if minutes == ['restart']:
                        print_text('Starting over.')
                        get_run_time(job)
                        break
                    job.minute.on(int(minutes[0]))
                    for minute in minutes[1:]:
                        job.minute.also.on(int(minute))

                elif setting == 'restart':
                    print_text('Starting over.')
                    get_run_time(job)
                    break

                else:
                    print_text('Your options are [i], [s], or [restart]. Restarting due to bad input.')
                    get_run_time(job)
                    break

            elif choice == 'restart':
                print_text('Starting over.')
                get_run_time(job)
                break

            else:
                print_text('Your options are [y], [n], or [restart]. Restarting due to bad input.')
                get_run_time(job)
                break

        elif c == 'restart':
            print_text('Starting over.')
            get_run_time(job)
            break

        else:
            print_text('Your options are [y], [n], or [restart]. Restarting due to bad input.')
            get_run_time(job)
            break

        print_text('Will this job run every hour of the day? y|n')
        c = input().lower()
        if c == 'y':
            pass

        elif c == 'n':
            print_text('Will this job run at only one hour of the day? y|n')
            choice = input().lower()
            if choice == 'y':
                print_text('What hour of the day will this job run? 0-23')
                hour = input()
                if hour == 'restart':
                    print_text('Starting over.')
                    get_run_time(job)
                    break
                job.hour.on(int(hour))

            elif choice == 'n':
                print_text('Will this job run in an hourly [i]nterval (every __ hours) or at [s]pecified hours of the day? i|s')
                period = input().lower()
                if period == 'i':
                    print_text('Every how many hours do you want this to run? 0-23')
                    interval = input()
                    if interval == 'restart':
                        print_text('Starting over.')
                        get_run_time(job)
                        break
                    job.hour.every(int(interval))

                elif period == 's':
                    print_text('What specific hours of the day do you want this to run? (comma delimited, no spaces) 0-23')
                    hours = input().split(',')
                    if hours == ['restart']:
                        print_text('Starting over.')
                        get_run_time(job)
                        break
                    job.hour.on(int(hours[0]))
                    for hour in hours[1:]:
                        job.hour.also.on(int(hour))

                elif period == 'restart':
                    print_text('Starting over.')
                    get_run_time(job)
                    break
                else:
                    print_text('Your options are [i], [s], or [restart]. Restarting due to bad input.')
                    get_run_time(job)
                    break

            elif choice == 'restart':
                print_text('Starting over.')
                get_run_time(job)
                break

            else:
                print_text('Your options are [y], [n], or [restart]. Restarting due to bad input.')
                get_run_time(job)
                break

        elif c == 'restart':
            print_text('Starting over.')
            get_run_time(job)
            break

        else:
            print_text('Your options are [y], [n], or [restart]. Restarting due to bad input.')
            get_run_time(job)
            break

        print_text('Will this job run every day of the week? y|n')
        c = input().lower()
        if c == 'y':
            pass
        elif c == 'n':
            day_of_week = True
            print_text('Does this job run only one day of the week? y|n')
            choice = input()
            if choice == 'y':
                print_text('What day of the week will it run? (0=Sun, 1=Mon, etc...) 0-6')
                week_day = input()
                if week_day == 'restart':
                    print_text('Starting over.')
                    get_run_time(job)
                    break
                job.dow.on(int(week_day))

            elif choice == 'n':
                print_text('Will this job run on an [i]nterval (every <n-th> day per week) or on [s]pecific days of the week? i|s')
                period = input().lower()
                if period == 'i':
                    week_interval = True
                    print_text('Every which day each week do you want this to run (every nth day)? 0-6')
                    interval = input()
                    if interval == 'restart':
                        print_text('Starting over.')
                        get_run_time(job)
                        break
                    job.dow.every(int(interval))

                elif period == 's':
                    print_text('What days of the week will it run? (comma delimited, no spaces) 0-6')
                    week_days = input().split(',')
                    if week_days == ['restart']:
                        print_text('Starting over.')
                        get_run_time(job)
                        break
                    job.dow.on(int(week_days[0]))
                    for day in week_days[1:]:
                        job.dow.also.on(int(day))

                elif period == 'restart':
                    print_text('Starting over.')
                    get_run_time(job)
                    break

                else:
                    print_text('Your options are [i], [s], or [restart]. Restarting due to bad input.')
                    get_run_time(job)
                    break

            elif choice == 'restart':
                print_text('Starting over.')
                get_run_time(job)
                break
            else:
                print_text('Your options are [y], [n], or [restart]. Restarting due to bad input.')
                get_run_time(job)
                break

        elif c == 'restart':
            print_text('Starting over.')
            get_run_time(job)
            break

        else:
            print_text('Your options are [y], [n], or [restart]. Restarting due to bad input.')
            get_run_time(job)
            break

        if day_of_week:
            print_text('Since you have specified a per-week schedule, do you want this to ONLY run on a per-week schedule?')
            print_text('(as opposed to a per-week AND per-month schedule) y|n')
            if week_interval:
                print_text('Keep in mind that since you have specified an interval of the week for the job to run,')
                print_text('choosing a per-month period to run will make the job called only when the schedule')
                print_text('matches BOTH your weekly interval AND your monthly scheduled time. For example: Running')
                print_text('every Friday if it is ALSO every 5th day of the month.')

        else:
            print_text('Will this job run every day of the month? y|n')

        c = input().lower()
        if c == 'y':
            pass
        elif c == 'n':
            print_text('Will this job run only once a month? y|n')
            choice = input().lower()

            if choice == 'y':
                print_text('What day of the month will it run on? 1-31')
                if day_of_week:
                    if week_interval:
                        print_text('Since you have specified a week-interval for this to run, this will run on both')
                        print_text('the day/days of the week you chose IF it is AlSO the day of the month you choose now.')
                    else:
                        print_text('Since you have specified day/days of the week for this to run, this will run on both')
                        print_text('the day/days of the week you chose AND the day of the month you choose now.')
                day = input()
                if day == 'restart':
                    print_text('Starting over.')
                    get_run_time(job)
                    break
                job.dom.on(int(day))

            elif choice == 'n':
                print_text('Will this job run on an [i]nterval (every __ days per month) or on [s]pecified days each month? i|s')
                period = input().lower()
                if period == 'i':
                    print_text('Every how many days per month will this to run? 0-31')
                    if day_of_week:
                        print_text('Since you have specified day/days of the week for this to run, this will run on')
                        print_text('the day/days of the week you chose IF it ALSO aligns with the interval that you')
                        print_text('specify now.')
                    interval = input()
                    if interval == 'restart':
                        print_text('Starting over.')
                        get_run_time(job)
                        break
                    job.dom.every(int(interval))

                elif period == 's':
                    print_text('What specific days of the month will this job run? (comma delimited, no spaces) 0-31')
                    if day_of_week:
                        print_text('Since you have specified day/days of the week for this to run, this will run on')
                        print_text('both the day/days of the week you chose AND the days of the month you choose now.')
                    specific = input().split(',')
                    if specific == ['restart']:
                        print_text('Starting over.')
                        get_run_time(job)
                        break
                    job.dom.on(int(specific[0]))
                    for day in specific[1:]:
                        job.dom.also.on(int(day))

                elif period == 'restart':
                    print_text('Starting over.')
                    get_run_time(job)
                    break

                else:
                    print_text('Your options are [i], [s], or [restart]. Restarting due to bad input.')
                    get_run_time(job)
                    break

            elif choice == 'restart':
                print_text('Starting over.')
                get_run_time(job)
                break

            else:
                print_text('Your options are [y], [n], or [restart]. Restarting due to bad input.')
                get_run_time(job)
                break

        elif c == 'restart':
            print_text('Starting over.')
            get_run_time(job)
            break

        else:
            print_text('Your options are [y], [n], or [restart]. Restarting due to bad input.')

        print_text('Will this job run every month of the year? y|n')
        c = input().lower()
        if c == 'y':
            pass

        elif c == 'n':
            print_text('Will this job run only one month of the year? y|n')
            choice = input().lower()
            if choice == 'y':
                print_text('What month will this run? 1-12')
                month = input()
                if month == 'restart':
                    print_text('Starting over.')
                    get_run_time(job)
                    break
                job.month.on(int(month))

            elif choice == 'n':
                print_text('Will this job run on an [i]nterval (every __ months per year) or on [s]pecific months? i|s')
                period = input().lower()
                if period == 'i':
                    print_text('Every how many months will this run? 1-12')
                    interval = input()
                    if interval == 'restart':
                        print_text('Starting over.')
                        get_run_time(job)
                        break
                    job.month.every(int(interval))

                elif period == 's':
                    print_text('What specific months will this job run? (comma delimited, no spaces) 1-12')
                    months = input().split(',')
                    if months == ['restart']:
                        print_text('Starting over.')
                        get_run_time(job)
                        break
                    job.month.on(int(months[0]))
                    for month in months[1:]:
                        job.month.also.on(int(month))

                elif period == 'restart':
                    print_text('Starting over.')
                    get_run_time(job)
                    break

                else:
                    print_text('Your options are [i], [s], or [restart]. Restarting due to bad input.')
                    get_run_time(job)
                    break

            elif choice == 'restart':
                print_text('Starting over.')
                get_run_time(job)
                break

            else:
                print_text('Your options are [y], [n], or [restart]. Restarting due to bad input.')
                get_run_time(job)
                break

        elif c == 'restart':
            print_text('Starting over.')
            get_run_time(job)
            break

        else:
            print_text('Your options are [y], [n], or [restart]. Restarting due to bad input.')

        break


def print_text(text):
    text = text
    for i in str(text):
        sys.stdout.write(i)
        sys.stdout.flush()
        time.sleep(0.01)
    print()


if __name__ == '__main__':
    main()
