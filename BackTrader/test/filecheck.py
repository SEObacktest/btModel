file_path = r"C:\Users\10643\OneDrive\桌面\工作\BackTrader\database\future_2024-12-23_14-10-41_mysql_data_xnBtm.sql\future_2024-12-23_14-10-41_mysql_data_xnBtm.sql"
try:
    with open(file_path, 'r', encoding='utf-8') as file:
        print("File is accessible and content is:")
        print(file.read(100))  # 读取前100个字符作为测试
except PermissionError:
    print("Permission denied. Please check the file permissions or run the script as administrator.")
except FileNotFoundError:
    print("File not found. Please check the file path.")
except Exception as e:
    print(f"An error occurred: {e}")