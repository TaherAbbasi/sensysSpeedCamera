from configparser import ConfigParser
import copy

class ConfigManager:
    """
    This class manages all configurable
    """
    def __init__(self, config_path):
        self.config = ConfigParser()
        self.config.read(config_path)
        self.changedItem = copy.deepcopy(self.config._sections)
        for sec in self.changedItem:
            for key in self.changedItem[sec]:
                self.changedItem[sec][key] = False

    def get_stream_component(self):
        ids = set()
        stream_component = list()
        for row in self.config['streaming_components']:
            sections = row.split("@")
            if "name" in sections:
                ids.add(sections[1])
        for stream_id in ids:
            stream_component.append({'name': self.config.get('streaming_components',
                                                          'streaming_component@{}@name'.format(stream_id)),
                        'id': self.config.get('streaming_components',
                                              'streaming_component@{}@id'.format(stream_id)),
                        'rest_url': self.config.get('streaming_components',
                                                    'streaming_component@{}@rest_url'.format(stream_id))
            })
        return stream_component

    def get_vision_component(self):
        ids = set()
        vision_component = list()
        for row in self.config['vision_components']:
            sections = row.split("@")
            if "name" in sections:
                ids.add(sections[1])
        for vision_id in ids:
            vision_component.append({'name': self.config.get('vision_components',
                                                          'vision_component@{}@name'.format(vision_id)),
                        'id': self.config.get('vision_components',
                                              'vision_component@{}@id'.format(vision_id)),
                        'rest_url': self.config.get('vision_components',
                                                    'vision_component@{}@rest_url'.format(vision_id))
            })
        return vision_component
    def get_active_stream_id(self, stream_component_id):
        """
        get ids of all active stream in config file
        """
        ids = set()
        for row in self.config['streaming_components']:
            sections = row.split("@")
            if "is_active" in sections and str(stream_component_id) in sections:
                value = int(self.config.get('streaming_components', row))
                if value is 1:
                    ids.add(sections[3])
        return ids

    def get_all_stream_id(self, stream_component_id):
        """
        get ids of all stream in config file
        """
        ids = set()
        for row in self.config['streaming_components']:
            # print(row)
            sections = row.split("@")
            if "is_active" in sections and str(stream_component_id) in sections: 
                ids.add(sections[3])
        return ids

    def get_app_config(self):
        return self.config

    def get_value(self, section, key):
        """return value of a config entry"""
        # b = self.config.get(section, key)
        # print("b = {} is type of {}".format(b,type(b)))
        # a = self._get_real_data(b)
        # print("a = {} is type of {}".format(a,type(a)))
        return self._get_real_data(self.config.get(section, key))
        
    def set_value(self, _section, _key, _val):
        if isinstance(_val, str):
            _val = '"' + _val + '"'
        else:
            _val = str(_val)
        self.config.set(_section, _key, _val)


    def _get_builtin_data(self, var):
        try:
            i = int(var)
            return i
        except:
            try:
                f = float(var)
                return f
            except:
                return var

    def _get_next_token(self, str_value):
        token = ""
        if str_value[0] == '[' or str_value[0] == ']':
            return str_value[0], str_value[1:]
        elif str_value[0] == '(' or str_value[0] == ')':
            return str_value[0], str_value[1:]
        elif str_value[0] == '"' or str_value[0] == '"':
            return str_value[0], str_value[1:]
            # index = str_value[1:].find('"')
            # return str_value[1:index-1], str_value[index:]
        elif str_value[0] == "'" or str_value[0] == "'":
            return str_value[0], str_value[1:]
            # index = str_value[1:].find("'")
            # return str_value[1:index-1], str_value[index:]
        else:
            remain_str = ""
            for index, char in enumerate(str_value):
                if (char != '[' and char != ']' and char != '(' and char != ')' 
                    and char != "'" and char != '"' and char != ','):
                    token += char
                else:
                    if char == ',':
                        remain_str = str_value[index+1:]
                    break
                remain_str = str_value[index+1:]
            return self._get_builtin_data(token), remain_str


    def _get_real_data(self, str_value):
        stack = []
        while len(str_value) > 0:
            next_token,str_value = self._get_next_token(str_value)
            if next_token == ']':
                temp_list = []
                for i in range(len(stack)):
                    top_var = stack.pop()
                    if(top_var == '['):
                        stack.append(temp_list)
                        break
                    else:
                        temp_list.insert(0,top_var)
            elif next_token == ')':    
                temp_list = []
                for i in range(len(stack)):
                    top_var = stack.pop()
                    if(top_var == ')'):
                        stack.append(tuple(temp_list))
                        break
                    else:
                        temp_list.insert(0,top_var)
            elif next_token == "'":
                pass
            elif next_token == '"':
                pass
            elif next_token != '':
                if isinstance(next_token, str):
                    if next_token.strip() != '' :
                        stack.append(next_token)
                else:
                    stack.append(next_token)
        return stack[0]            

    def update_configs(self, new_config_dict):
        """"set configs to new config"""
        for sec in new_config_dict:
            for key in new_config_dict[sec]:
                if new_config_dict[sec][key] != self.config.get(sec, key):
                    self.changedItem[sec][key] = True
        self.config.read_dict(new_config_dict)

    def clear_change_history(self):
        """change history of changing option value"""
        self.changedItem = copy.deepcopy(self.config._sections)
        for sec in self.changedItem:
            for key in self.changedItem[sec]:
                self.changedItem[sec][key] = False

    def save_new_config_on_file(self, config_file_path):
        """save current config on disk as INI file"""
        with open(config_file_path, 'w') as f:
            self.config.write(f)
    

    # def add_violation(self, _code, _title, _desc, _val):
    #     val = self.get_value('violations', 'violations_number')
    #     self.set_value('violations', 'violations_number', val + 1)
    #     self.config.

    def remove_violation(self, _code):
        pass

    def set_default_violation(self, _code):
        pass