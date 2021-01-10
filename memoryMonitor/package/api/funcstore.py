from functools import reduce
import datetime
import nuke


def nk_value(element):
    """Retrieve a value from Nuke memory info and return it as a rounded MB one.
    @param (str) element:
    The name of the info this function needs to retrieve.
    @return (float) round_data:
    The memory value, expressed in MB.
    """
    data = (nuke.memory(element)) * 0.000001
    round_data = round(data, 2)
    return round_data


def ram_percentage(n):
    """Returns a percentage of a number against the total RAM allocated by Nuke.
    @param (float) n:
    A memory value
    @return (float) round_percentage:
    The percentage of total RAM allocated used by user.
    """
    total_ram = nk_value('max_usage')
    percentage = (n / total_ram) * 100
    round_percentage = round(percentage, 2)
    return round_percentage


def find_multiplier(n):
    """Takes a number and returns a factor to be used for monitor chart ticks.
    @param (int) n:
    Number.
    @return (int) factors_list[x]:
    The factor deemed appropriate for use.
    """
    factors_list = sorted(reduce(list.__add__,
                                 ([i, n // i] for i in range(1, int(n ** 0.5) + 1) if n % i == 0)))
    if len(factors_list) <= 3:
        return factors_list[-1]
    else:
        return factors_list[-2]


class ListsModifier:
    def __init__(self, mem_list, dt_list, max_int):
        """A class to modify Monitor memory and date time lists.
        @param (list) mem_list:
        Monitor's memory list.
        @param (list) dt_list:
        Monitor's date-time list.
        @param (int) max_int:
        Monitor's maximum allowance for the length of both lists.
        @return (None):
        No return value.
        """
        self.mem_list = mem_list
        self.dt_list = dt_list
        self.max_int = max_int

    def update(self):
        """Update method that will append both lists with 'usage' memory value and current date time.
        If the lists lengths are higher than max_int, the function will delete the first elements in the lists
        before appending new ones.
        """
        length = len(self.mem_list) - 1
        current_dt = datetime.datetime.now().strftime("%x - %X")
        if length <= self.max_int:
            self.mem_list.append(nk_value('usage'))
            self.dt_list.append(current_dt)
        else:
            self.mem_list.pop(0)
            self.dt_list.pop(0)
            self.update()

    def resize(self):
        """To be invoked if the user change the maximum allowance number aka the max sample number. If the lists
        lengths are higher than the new max number, the function will delete members of the lists starting by the
        first ones. If the lists lengths are lower, then both lists will be appended with blank values until their
        lengths match the new max number
        """
        if len(self.mem_list) > (self.max_int + 1):
            while len(self.mem_list) > (self.max_int + 1):
                self.mem_list.pop(0)
                self.dt_list.pop(0)
                if len(self.mem_list) == (self.max_int + 1):
                    break
        elif len(self.mem_list) < (self.max_int + 1):
            while len(self.mem_list) < (self.max_int + 1):
                self.mem_list.append(0)
                self.dt_list.append("---")
                if len(self.mem_list) == (self.max_int + 1):
                    break
