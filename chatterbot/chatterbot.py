from .controllers import StorageController
from .conversation import Response, Statement, Signature
from .utils.module_loading import import_module


class ChatBot(object):

    def __init__(self, name, **kwargs):
        self.name = name

        storage_adapter = kwargs.get("storage_adapter",
            "chatterbot.adapters.storage.JsonDatabaseAdapter"
        )

        logic_adapter = kwargs.get("logic_adapter",
            "chatterbot.adapters.logic.ClosestMatchAdapter"
        )

        io_adapter = kwargs.get("io_adapter",
            "chatterbot.adapters.io.TerminalAdapter"
        )

        self.storage = StorageController(storage_adapter, **kwargs)

        LogicAdapter = import_module(logic_adapter)
        self.logic = LogicAdapter()

        IOAdapter = import_module(io_adapter)
        self.io = IOAdapter()

    def train(self, conversation):
        for statement in conversation:
            self.storage.train(statement)

    def get_response_data(self, data):
        """
        Returns a dictionary containing the meta data for
        the current response.
        """
        if "text" in data:
            text_of_all_statements = self.storage.list_statements()

            match = self.logic.get(data["text"], text_of_all_statements)

            if match:
                response = self.storage.get_most_frequent_response(match)
            else:
                response = self.storage.get_random_statement()

        else:
            # If the input is blank, return a random statement
            response = self.storage.get_random_statement()

        statement = list(response.keys())[0]
        values = response[statement]

        previous_statement = self.storage.get_last_statement()
        response_list = self.storage.update_response_list(statement, previous_statement)

        count = self.storage.update_occurrence_count(values)

        name = data["name"]

        values["name"] = name
        values["occurrence"] = count
        values["in_response_to"] = response_list

        self.storage.recent_statements.append(list(response.keys())[0])

        response_data = {
            name: {
                data["text"]: values
            },
            "bot": response
        }

        # Update the database before selecting a response
        self.storage.save_statement(**response_data[name])

        return response_data

    def get_response(self, input_text, user_name="user"):
        """
        Return the bot's response based on the input.
        """
        response_data = self.get_response_data(
            {"name":user_name, "text": input_text}
        )

        response = self.io.process_response(response_data)

        return response

    def get_input(self):
        return self.io.process_input()

