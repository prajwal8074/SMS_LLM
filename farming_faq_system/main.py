from database import FAQDatabase
from file_manager import FAQFileManager

def main():
    print("Farming FAQ System\n")
    faq_system = FAQDatabase()
    
    while True:
        print("\nMenu:")
        print("1. Search FAQ")
        print("2. Add FAQ")
        print("3. Backup/Restore")
        print("4. Import/Export")
        print("5. Exit")
        
        choice = input("Select option: ")
        
        if choice == "1":
            question = input("\nEnter question: ")
            answer = faq_system.get_answer(question)
            print(f"\nAnswer: {answer if answer else 'Not found'}")
            
        elif choice == "2":
            question = input("\nNew question: ")
            answer = input("Answer: ")
            category = input("Category [General]: ") or "General"
            faq_system.add_faq(question, answer, category)
            print("FAQ added!")
            
        elif choice == "3":
            print("\n1. Create backup")
            print("2. Restore backup")
            sub = input("Select: ")
            
            if sub == "1":
                path = faq_system.file_manager.create_backup()
                print(f"Backup created at {path}")
            elif sub == "2":
                backups = sorted(os.listdir("data/backups"))
                print("Available backups:")
                for i, b in enumerate(backups, 1):
                    print(f"{i}. {b}")
                sel = int(input("Select backup: ")) - 1
                faq_system.file_manager.restore_backup(backups[sel])
                print("Restore complete!")
                
        elif choice == "4":
            print("\n1. Export to JSON")
            print("2. Export to CSV")
            sub = input("Select: ")
            
            if sub == "1":
                path = faq_system.file_manager.export_to_json()
                print(f"Exported to {path}")
            elif sub == "2":
                path = faq_system.file_manager.export_to_csv()
                print(f"Exported to {path}")
                
        elif choice == "5":
            print("Goodbye!")
            break

if __name__ == "__main__":
    main()