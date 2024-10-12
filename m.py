import requests
import json
import time
import datetime
import os
from colorama import Fore, Style, init

init(autoreset=True)

def print_welcome_message():
    print(Fore.WHITE + r"""
_  _ _   _ ____ ____ _    ____ _ ____ ___  ____ ____ ___ 
|\ |  \_/  |__| |__/ |    |__| | |__/ |  \ |__/ |  | |__]
| \|   |   |  | |  \ |    |  | | |  \ |__/ |  \ |__| |         
          """)
    print(Fore.GREEN + Style.BRIGHT + "Nyari Airdrop Moonhub by Moongate")
    print(Fore.YELLOW + Style.BRIGHT + "Telegram: https://t.me/nyariairdrop")

def load_accounts():
    with open('data.txt', 'r') as file:
        return [line.strip() for line in file if line.strip()]

def process_account(auth):
    headers = {
        'authorization': auth,
        'accept': 'application/json, text/plain, */*',
        'origin': 'https://tg.moongate.app',
        'referer': 'https://tg.moongate.app/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0'
    }

    # Profile
    response = requests.get('https://tg-api.moongate.app/api/v1/user/profile?refBy=', headers=headers)
    if response.status_code == 200:
        profile = response.json()
        print(Fore.CYAN + f"Profil: {profile['username']} ({profile['first_name']})")
        print(Fore.CYAN + f"Level: {profile['user_level']}")
        print(Fore.CYAN + f"Poin saat ini: {profile['current_point']}")
        print(Fore.CYAN + f"Total poin: {profile['total_point']}")
        print(Fore.CYAN + f"Poin per jam: {profile['point_per_hour']}")
        print(Fore.CYAN + f"Maks. jam mining: {profile['max_mine_hour']}")
        print(Fore.CYAN + f"Kode referral: {profile['ref_code']}")
        print(Fore.CYAN + f"Total referral: {profile['total_ref_count']}")
        print(Fore.CYAN + f"Total poin referral: {profile['total_ref_point']}")
        print(Fore.CYAN + f"Streak check-in: {profile['checkin_streak']}")
        print(Fore.CYAN + f"Total check-in: {profile['total_checkin']}")
        
        # Optimisasi berdasarkan profil
        optimize_mining(headers, profile)
        optimize_referrals(headers, profile)
    else:
        print(Fore.RED + "Gagal mengambil profil")
        return

    # Check-in harian
    daily_check_in(headers)

    # Task list dan proses task
    process_tasks(headers)

def optimize_mining(headers, profile):
    current_time = datetime.datetime.now()
    if profile['last_synced_point']:
        last_synced = profile['last_synced_point'].replace('Z', '')  # Remove 'Z'
        last_synced = datetime.datetime.fromisoformat(last_synced)  # Convert to datetime
    else:
        last_synced = None

    if not last_synced or (current_time - last_synced).total_seconds() / 3600 >= profile['max_mine_hour']:
        # Klaim poin jika sudah waktunya
        payload = {"pointClaimed": 0, "updateTime": int(current_time.timestamp() * 1000)}
        response = requests.post('https://tg-api.moongate.app/api/v1/user/claim', headers=headers, json=payload)
        if response.status_code == 201:
            claimed_points = profile['point_per_hour'] * profile['max_mine_hour']
            print(Fore.GREEN + f"Klaim berhasil. Poin diperoleh: {claimed_points}")
        else:
            print(Fore.RED + "Gagal melakukan klaim")
    else:
        time_left = profile['max_mine_hour'] - (current_time - last_synced).total_seconds() / 3600
        print(Fore.YELLOW + f"Belum waktunya klaim. Sisa waktu: {time_left:.2f} jam")


def optimize_referrals(headers, profile):
    if profile['ref_claimable'] > 0:
        response = requests.post('https://tg-api.moongate.app/api/v1/user/claim-ref', headers=headers)
        if response.status_code == 200:
            print(Fore.GREEN + f"Klaim referral berhasil. Poin diperoleh: {profile['ref_claimable']}")
        else:
            print(Fore.RED + "Gagal melakukan klaim referral")
    else:
        print(Fore.YELLOW + "Tidak ada poin referral yang dapat diklaim")


def process_tasks(headers):
    response = requests.get('https://tg-api.moongate.app/api/v1/task/list', headers=headers)
    if response.status_code == 200:
        tasks = response.json()

        # Pastikan 'tasks' bukan None dan merupakan list
        if tasks and isinstance(tasks, list):
            print(Fore.YELLOW + f"Jumlah tugas: {len(tasks)}")
            for task in tasks:
                # Periksa apakah 'task_user' ada atau None
                task_user = task.get('task_user')
                if task_user is None:
                    # Jika 'task_user' None, berarti tugas belum diproses (anggap belum selesai)
                    print(Fore.YELLOW + f"Tugas belum diproses: {task['name']}. Memulai proses tugas...")
                    process_task(headers, task)
                elif 'status' in task_user and task_user['status'] == "DONE":
                    # Jika 'task_user' ada dan status 'DONE', tugas sudah selesai
                    print(Fore.CYAN + f"Tugas sudah selesai: {task['name']}. Reward: {task_user['reward_amount']}")
                else:
                    # Jika ada 'task_user' tapi belum 'DONE', proses tugas
                    process_task(headers, task)
        else:
            print(Fore.RED + "Daftar tugas kosong atau tidak valid.")
    else:
        print(Fore.RED + "Gagal mengambil daftar tugas")


def process_task(headers, task):
    task_id = task['_id']
    
    # Cek apakah 'task_user' ada dan valid sebelum diproses
    task_user = task.get('task_user')
    if task_user is None or task_user.get('status') != "DONE":
        # Jika 'task_user' None atau belum selesai, proses tugas
        response = requests.put(f'https://tg-api.moongate.app/api/v1/task/{task_id}', headers=headers)
        if response.status_code == 200:
            print(Fore.YELLOW + f"Memproses tugas: {task['name']}")
        else:
            print(Fore.RED + f"Gagal memproses tugas: {task['name']}")
            return

        # Check task completion
        response = requests.post(f'https://tg-api.moongate.app/api/v1/task/check/{task_id}', headers=headers)
        if response.status_code == 201:
            result = response.json()
            print(Fore.GREEN + f"Tugas selesai: {task['name']}. Reward: {result['reward_amount']}")
        else:
            print(Fore.RED + f"Gagal menyelesaikan tugas: {task['name']}")
    else:
        print(Fore.YELLOW + f"Tugas sudah selesai: {task['name']}. Tidak perlu diproses lagi.")


def daily_check_in(headers):
    # Mendapatkan info dari endpoint daily check-in
    response = requests.get('https://tg-api.moongate.app/api/v1/task/daily', headers=headers)
    if response.status_code == 200:
        daily_info = response.json()
        
        # Mendapatkan tanggal terakhir check-in dan mengonversinya ke format datetime
        last_checkin_day = daily_info.get('last_checkin_day')
        if last_checkin_day:
            # Mengonversi last_checkin_day ke datetime
            last_checkin_date = datetime.datetime.fromisoformat(last_checkin_day.replace('Z', ''))
            today = datetime.datetime.now().date()
            
            # Cek apakah sudah check-in hari ini
            if last_checkin_date.date() == today:
                print(Fore.YELLOW + "Check-in sudah dilakukan hari ini. Tidak perlu check-in lagi.")
                return  # Keluar dari fungsi jika sudah check-in
            else:
                print(Fore.GREEN + "Belum check-in hari ini. Melanjutkan check-in.")
        else:
            print(Fore.YELLOW + "Informasi check-in tidak ditemukan. Melanjutkan check-in.")
        
        # Menampilkan informasi total check-in harian
        print(Fore.GREEN + f"Total hari check-in: {daily_info['total_checkin_days']}")
        
        # Jika ada poin tambahan dari check-in harian, tampilkan juga
        if 'reward_amount' in daily_info:
            print(Fore.GREEN + f"Reward dari check-in harian: {daily_info['reward_amount']}")
        
        # Lanjutkan dengan proses check-in jika belum dilakukan hari ini
        response = requests.get('https://tg-api.moongate.app/api/v1/task/checkin', headers=headers)
        if response.status_code == 200:
            checkin_result = response.json()
            print(Fore.GREEN + f"Check-in berhasil. Total hari check-in sekarang: {checkin_result['total_checkin_days']}")
        else:
            print(Fore.RED + "Gagal melakukan check-in")
    else:
        print(Fore.RED + "Gagal mengambil informasi check-in harian")


def get_optimal_wait_time(accounts):
    min_wait_time = float('inf')
    for auth in accounts:
        headers = {
            'authorization': auth,
            'accept': 'application/json, text/plain, */*',
            'origin': 'https://tg.moongate.app',
            'referer': 'https://tg.moongate.app/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0'
        }
        response = requests.get('https://tg-api.moongate.app/api/v1/user/profile?refBy=', headers=headers)
        if response.status_code == 200:
            profile = response.json()
            max_mine_hour = profile['max_mine_hour']
            min_wait_time = min(min_wait_time, max_mine_hour)
    
    # Tambahkan sedikit buffer (misalnya 5 menit) untuk memastikan semua akun siap
    return min_wait_time * 3600 + 300  # konversi ke detik dan tambah 5 menit


def main():
    print_welcome_message()
    accounts = load_accounts()
    print(Fore.BLUE + f"Jumlah akun: {len(accounts)}")

    while True:
        for i, auth in enumerate(accounts, 1):
            print(Fore.YELLOW + f"\nMemproses akun {i}/{len(accounts)}")
            try:
                process_account(auth)
            except Exception as e:
                print(Fore.RED + f"Error pada akun {i}: {str(e)}")
            time.sleep(5)  # Jeda 5 detik antar akun


        optimal_wait_time = get_optimal_wait_time(accounts)
        print(Fore.MAGENTA + f"\nSemua akun telah diproses. Menunggu {optimal_wait_time/3600:.2f} jam sebelum memulai kembali.")
        
        # Hitung mundur waktu optimal
        target_time = datetime.datetime.now() + datetime.timedelta(seconds=optimal_wait_time)
        while datetime.datetime.now() < target_time:
            remaining_time = target_time - datetime.datetime.now()
            hours, remainder = divmod(remaining_time.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            countdown = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            print(Fore.CYAN + f"\rWaktu tersisa: {countdown}", end="", flush=True)
            time.sleep(1)
        
        print(Fore.GREEN + "\nMemulai proses kembali...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nProgram dihentikan oleh pengguna.")
    except Exception as e:
        print(Fore.RED + f"Terjadi kesalahan: {str(e)}")
        print(Fore.YELLOW + "Program akan melanjutkan tugas lainnya.")
