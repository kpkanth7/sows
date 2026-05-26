from db import get_client

def main():
    sb = get_client()
    try:
        # Delete everything
        res = sb.table('news_items').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        print(f"Deleted rows")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
