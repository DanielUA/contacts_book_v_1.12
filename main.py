from collections import UserDict
from datetime import date, datetime
import os
import pickle


class Field():
    def __init__(self, value):
        if not self.valid(value):
            raise ValueError("Incorrect value")
        self.__value = value
    
    def valid(self, value):
        return True
 
    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        if not self.valid(value):
            raise ValueError("Incorrect value")
        self.__value = value

class Name(Field):
    def valid(self, value):
        return value.isalpha()


class Phone(Field):
    def valid(self, value):
        if not (len(value) == 10 and value.isdigit()):
            return False
        return True


class Birthday(Field):
    def valid(self, value):
        try:
            datetime.strptime(value, "%d.%m.%Y")
            return True
        except ValueError:
            return False 


class Record:
    def __init__(self, name, birthday=None):
        self.name = Name(name)
        self.phones = []
        self.birthday = Birthday(birthday) if birthday is not None else None

    def days_to_birthday(self):
        if self.birthday is None:
            return "no data of birthday"
        day_now = date.today()
        str_date = self.birthday.value
        try:
            birth_update = datetime.strptime(str_date, "%d.%m.%Y")
            year_birthday = birth_update.replace(year=day_now.year)
            days_until_birthday = (year_birthday - day_now).days
            if days_until_birthday < 0:
                year_birthday = birth_update.replace(year=day_now.year + 1)
                days_until_birthday = (year_birthday - day_now).days
            return days_until_birthday
        except ValueError:
            return "Incorrect date format"

    def add_phone(self, phone_number):
        self.phones.append(Phone(phone_number))

    def remove_phone(self, phone_number):
        self.phones = [phone for phone in self.phones if phone.value != phone_number]

    def edit_phone(self, old_number, new_number):
        for phone in self.phones:
            if phone.value == old_number:
                phone.value = new_number
                phone.valid(new_number)
                return 
        raise ValueError(f"Invalid phone number: {old_number}")

    def find_phone(self, phone_number):
        return next((phone for phone in self.phones if phone.value == phone_number), None)
    
    def find_user_by_phone_name(self, query):
        query = query.lower()
        if query.isdigit():
            for phone in self.phones:
                if query in phone.value:
                    return str(self)
        elif query.isalpha():
            if query in self.name.value.lower():
                return str(self)
        return None

    def __str__(self):
        phones_str = '; '.join(str(phone.value) for phone in self.phones)
        return f"Contact name: {self.name.value}, phones: {phones_str}"

class AddressBook(UserDict):
    def __init__(self, file=None):
        super().__init__()
        self.file = file

    def get_full_file_path(self):
        if self.file:
            return os.path.join(os.getcwd(), self.file)
        else:
            print("File not specified. Unable to get the full file path.")
            return None

    def iterator(self, n):
        values = list(self.data.values())
        for i in range(0, len(values), n):
            yield values[i:i + n]

    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name, None)

    def delete(self, name):
        if name in self.data:
            del self.data[name]
    
    def save_address_book(self):
        full_file_path = self.get_full_file_path()
        if full_file_path:
            with open(full_file_path, "wb") as fh:
                pickle.dump(self, fh)
            print(f"Address book saved successfully to '{full_file_path}'.")

    def load_address_book(self):
        full_file_path = self.get_full_file_path()
        if full_file_path:
            if os.path.exists(full_file_path):
                with open(full_file_path, "rb") as fh:
                    content = pickle.load(fh)
                print(f"Address book loaded successfully from '{full_file_path}'.")
                return content
            else:
                print(f"File '{full_file_path}' not found. Creating a new address book.")
                return self
        else:
            print("File not specified. Unable to load the address book.")
            return None

    def search(self, query):
        result = []
        for record in self.data.values():
            found_user = record.find_user_by_phone_name(query)
            if found_user:
                result.append(found_user)
        return result

# Завантаження адресної книги при старті програми
book = AddressBook()
loaded_book = book.load_address_book()
if loaded_book:
    book = loaded_book

def input_error(func):
    def wrapper(command):
        try:
            return func(command)
        except (TypeError) as e:
            return f"Input error of type: {e}"
        except (IndexError) as e:
            return f"Input error: {e}"
        except (ValueError) as e:
            return f"Input 3 arguments only(example: command name phone): {e}"
        except (KeyError) as e:
            return f"Input error: {e}"
        except Exception as e:
            return f"Command error"
    return wrapper

@input_error
def add(command):
    com, name, phone = command.split()
    if not com == "add":
        raise Exception("Incorrect command name, try again")
    if name in book.data:
        raise KeyError("This name is exist")
    
    new_record = Record(name)
    new_record.add_phone(phone)
    book.add_record(new_record)
    book.save_address_book()  # Збереження адресної книги при додаванні нового запису
    return "Record added successfully."

@input_error
def change(command):
    com, name, phone = command.split()
    if not com == "change":
        raise Exception("Incorrect command name, try again")
    if not name in book.data:
        raise KeyError("This name is not exist")
    
    record = book.find(name)
    record.edit_phone(record.phones[0].value, phone)
    book.save_address_book()  # Збереження адресної книги при зміні номера телефону
    return "Phone number changed successfully."

@input_error
def phone(command):
    com, name = command.split()
    if not com == "phone":
        raise Exception("Incorrect command name, try again")
    if not name in book.data:
        raise KeyError("This name is not exist")
    
    record = book.find(name)
    return f"{record.name.value} has phone {record.phones[0].value}"

@input_error
def show_all(command):
    if command != "show all":
        raise Exception("Incorrect command name, try again")
    result = [str(record) for record in book.data.values()]        
    return "\n".join(result)

COMMANDS = {   
    "add": add,
    "change": change,
    "phone": phone,
    "show all": show_all,
}

@input_error
def command_action(command):
    for el in COMMANDS:
        if command.startswith(el):
            return COMMANDS[el]
    raise Exception("Incorrect command name, try again")

def main():
    while True:
        command = input("Enter your command: ").lower()
        if command in ["good bye", "close", "exit", "."]:
            print("Good bye!")
            break
        elif command == "hello":
            print("How can I help you?")
            continue
        func = command_action(command)
        if func == "Command error":         
            print(func)
            continue
        result = func(command)
        if result == "break":
            break
        elif result:
            print(result)

if __name__ == "__main__":
    main()


# Створення нової адресної книги
book = AddressBook()

# Створення запису для John
john_record = Record("John")
john_record.add_phone("1234567890")
john_record.add_phone("5555555555")

# Додавання запису John до адресної книги
book.add_record(john_record)

# Створення та додавання нового запису для Jane
jane_record = Record("Jane")
jane_record.add_phone("9876543210")
book.add_record(jane_record)

# Виведення всіх записів у книзі
for name, record in book.data.items():
    print(record)

# Знаходження та редагування телефону для John
john = book.find("John")
john.edit_phone("1234567890", "1112223333")

print(john)  # Виведення: Contact name: John, phones: 1112223333; 5555555555

# Пошук конкретного телефону у записі John
found_phone = john.find_phone("5555555555")

# Видалення запису Jane
book.delete("Jane")

# Збереження адресної книги на диск
book.file = "address_book.pkl"
book.save_address_book()

# Відновлення адресної книги з диска
restored_book = AddressBook(file="address_book.pkl")
restored_book.load_address_book()

# Пошук у відновленій адресній книзі за номером телефону або ім'ям
search_result = restored_book.search("555")

