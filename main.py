from collections import UserDict
from datetime import date, datetime
from abc import ABC, abstractmethod
import os
import pickle
import sys

class UserInterface(ABC):
    @abstractmethod
    def display_information(self, information):
        pass

class ConsoleUserInterface(UserInterface):
    def display_information(self, information):
        print(information)

class Field:
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
        return len(value) == 10 and value.isdigit()


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
    def __init__(self, file=None, user_interface = None):
        super().__init__()
        self.file = file
        self.user_interface = user_interface if user_interface else ConsoleUserInterface()

    def set_user_interface(self, user_interface):
        self.user_interface = user_interface 

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
        if full_file_path := self.get_full_file_path():
            with open(full_file_path, "wb") as fh:
                pickle.dump(self.data, fh)
            self.user_interface.display_information(f"Address book saved successfully to '{full_file_path}'.")

    def load_address_book(self):
        if full_file_path := self.get_full_file_path():
            if os.path.exists(full_file_path):
                with open(full_file_path, "rb") as fh:
                    content = pickle.load(fh)
                print(f"Address book loaded successfully from '{full_file_path}'.")
                return content
            else:
                print(f"File '{full_file_path}' not found. Creating a new address book.")
                return {}
        else:
            print("File not specified. Unable to load the address book.")
            return {}

    def search(self, query):
        result = []
        for el in self.data.values():
            if found_user := el.find_user_by_phone_name(query):
                result.append(found_user)
        return result


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
            return "Command error"

    return wrapper


@input_error
def add(command):
    com, name, phone = command.split()
    if com != "add":
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
    if com != "change":
        raise Exception("Incorrect command name, try again")
    if name not in book.data:
        raise KeyError("This name is not exist")

    record = book.find(name)
    record.edit_phone(record.phones[0].value, phone)
    book.save_address_book()  # Збереження адресної книги при зміні номера телефону
    return "Phone number changed successfully."


@input_error
def phone(command):
    com, name = command.split()
    if com != "phone":
        raise Exception("Incorrect command name, try again")
    if name not in book.data:
        raise KeyError("This name is not exist")

    record = book.find(name)
    return f"{record.name.value} has phone {record.phones[0].value}"


def show_all(com):
    if com != "show all":
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

book = AddressBook(file="example.pkl")
book.data = book.load_address_book()

def main():
    print("Welcome to the Address Book Program!")
    print("Available commands:")
    print("1. add <name> <phone> - Add a new record to the address book.")
    print("2. change <name> <phone> - Change the phone number of an existing record.")
    print("3. phone <name> - Retrieve the phone number for a specific name.")
    print("4. show all - Display all records in the address book.")
    print("5. search <query> - Search for records based on a query.")
    print("6. hello - Display a welcome message.")
    print("7. good bye, close, exit, . - Exit the program.")

    while True:
        print()
        command = input("Enter your command: ").lower()
        if command in ["good bye", "close", "exit", "."]:
            # Save the address book before exiting the program
            book.save_address_book()
            book.user_interface.display_information("Good bye!")
            sys.exit()

        elif command == "hello":
            book.user_interface.display_information("How can I help you?")
            continue

        elif command.startswith("search"):
            query = command.split(" ", 1)[1]  # Extract the search query
            results = book.search(query)
            if results:
                book.user_interface.display_information("Search Results:")
                for result in results:
                    book.user_interface.display_information(result)
            else:
                book.user_interface.display_information("No matching records found.")

        else:
            func = command_action(command)
            if func == "Command error":
                book.user_interface.display_information(func)
                continue
            result = func(command)
            if result == "break":
                sys.exit()
            elif result:
                book.user_interface.display_information(result)


if __name__ == "__main__":
    console_ui = ConsoleUserInterface()
    book = AddressBook(file="example.pkl", user_interface=console_ui)
    book.data = book.load_address_book()
    main()
