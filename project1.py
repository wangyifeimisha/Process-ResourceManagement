import io
import sys



class rcb:
    def __init__(self,n):
        self.state = n
        self.inventory = n
        self.waitlist = []

class pcb:
    def __init__(self,parent,rank):
        self.state = 1
        self.parent = parent
        self.rank = rank
        self.children = []
        self.resource = []


class shell:

    def __init__(self,filename):
        self.__COMMANDS = {'cr':self.create,
                      'de':self.destory,
                      'rq':self.request,
                      'rl':self.release,
                      'to':self.timeout,
                      'in':self.init}

        self.pcb_limit = 16
        self.rcb_list = None
        self.pcb_list = None
        self.rl = None
        self.runing_process = None
        self.initial_number = 0
        input_f = io.open(filename, "r", encoding='utf-8')
        for line in input_f:
            if line.strip()[:2] != "//" and line.strip() != '' :
                clean_line = line.strip().split()
                if len(clean_line) == 1:
                    self.__COMMANDS[clean_line[0]]()
                elif len(clean_line) == 2:
                    self.__COMMANDS[clean_line[0]](clean_line[1])
                elif len(clean_line) == 3:
                    self.__COMMANDS[clean_line[0]](clean_line[1],clean_line[2])
                else:
                    continue

        input_f.close()

    def init(self):
        if self.initial_number != 0:
            print()
        self.initial_number += 1
        self.pcb_list = [-1]*self.pcb_limit
        self.rcb_list = [rcb(1),rcb(1),rcb(2),rcb(3)]
        initial_pcb = pcb(-1,0)
        self.rl = [[initial_pcb],[],[]]
        self.pcb_list[0] = initial_pcb
        self.runing_process = initial_pcb

        self.scheduler()


    def create(self,rank):
        rank = int(rank)
        if rank > 0 and rank <= 2 and -1 in self.pcb_list:
            index = self.pcb_list.index(-1)
            new_pcb = pcb(self.pcb_list.index(self.runing_process),rank)
            self.pcb_list[index] = new_pcb
            self.rl[rank] += [new_pcb]
            self.runing_process.children += [new_pcb]
            self.scheduler()

        else:
            print('-1',end = " ")


    def __get_destory_list(self,index):
        destory_list = [self.pcb_list[index]]
        for c in self.pcb_list[index].children:
            destory_list += self.__get_destory_list(self.pcb_list.index(c))

        return destory_list



    def destory(self,index):
        index = int(index)
        destory_list = []

        destory_children_process = []
        for i in self.runing_process.children:
            if i in self.pcb_list:
                destory_children_process += [self.pcb_list.index(i)]

        if index in destory_children_process:
            destory_list += self.__get_destory_list(index)
            for i in destory_list:
                self.pcb_list[self.pcb_list.index(i)] = -1
                if i.state == 1:
                    del self.rl[i.rank][self.rl[i.rank].index(i)]
                    if i.resource != []:
                        for (res, units) in i.resource:
                            self.rcb_list[res].state += units
                            another_waitlist = []
                            for (units_need, wait_pcb) in self.rcb_list[res].waitlist:
                                if wait_pcb not in destory_list and units_need <= self.rcb_list[res].state:
                                    self.rcb_list[res].state -= units_need
                                    another_waitlist += [(units_need, wait_pcb)]
                                    wait_pcb.state = 1
                                    wait_pcb.resource += [(res, units_need)]
                                    self.rl[wait_pcb.rank] += [wait_pcb]
                            for delete in another_waitlist:
                                del self.rcb_list[res].waitlist[self.rcb_list[res].waitlist.index(delete)]

                else:
                    for j in self.rcb_list:
                        delete_waitlist = []
                        for (n,pcb) in j.waitlist:
                            if i == pcb:
                                delete_waitlist += [(n,pcb)]
                                if pcb.resource != []:
                                    for (res,units) in pcb.resource:
                                        self.rcb_list[res].state += units
                                        another_waitlist = []
                                        for (units_need, wait_pcb) in self.rcb_list[res].waitlist:
                                            if wait_pcb not in destory_list and units_need <= self.rcb_list[res].state:
                                                self.rcb_list[res].state -= units_need
                                                another_waitlist += [(units_need, wait_pcb)]
                                                wait_pcb.state = 1
                                                wait_pcb.resource += [(res,units_need)]
                                                self.rl[wait_pcb.rank] += [wait_pcb]
                                        for delete in another_waitlist:
                                            del self.rcb_list[res].waitlist[self.rcb_list[res].waitlist.index(delete)]
                        for k in delete_waitlist:
                            del j.waitlist[j.waitlist.index(k)]
            self.scheduler()
        else:
            print("-1",end = " ")



    def request(self,r,n):
        r = int(r)
        n = int(n)

        if self.pcb_list.index(self.runing_process) != 0 and r >=0 and r <= 3:
            if n >= 0 and n <= self.rcb_list[r].state:
                self.rcb_list[r].state -= n
                if r in [res for (res,units) in self.runing_process.resource]:
                    for (res,units) in self.runing_process.resource:
                        if r == res:
                            self.runing_process.resource[self.runing_process.resource.index((res,units))] = (r,n+units)
                else:
                    self.runing_process.resource += [(r,n)]
                self.scheduler()

            elif n >= 0 and n <= self.rcb_list[r].inventory:
                if r in [res for (res,units) in self.runing_process.resource]:
                    for (res,units) in self.runing_process.resource:
                        if r == res:
                            if n+units > self.rcb_list[r].inventory:
                                print("-1",end=' ')
                                return

                self.runing_process.state = 0
                self.rcb_list[r].waitlist += [(n,self.runing_process)]
                del self.rl[self.runing_process.rank][self.rl[self.runing_process.rank].index(self.runing_process)]
                self.scheduler()
            else:
                print("-1",end = " ")
        else:
            print("-1",end =" ")


    def release(self,r,n):
        r = int(r)
        n = int(n)
        if self.runing_process.resource != []:
            resource_location = -1
            for (i,j) in self.runing_process.resource:
                if r == i:
                    resource_location = self.runing_process.resource.index((i,j))
            if resource_location != -1:
                res = self.runing_process.resource[resource_location][0]
                units = self.runing_process.resource[resource_location][1]
                if n <= units:
                    self.rcb_list[res].state += units
                    self.runing_process.resource[resource_location] = (res,units-n)
                    if n == res:
                        del self.runing_process.resource[resource_location]
                    if self.rcb_list[res].waitlist != []:
                        delete_waitlist = []
                        for (units_need,pcb) in self.rcb_list[res].waitlist:
                            if units_need <= self.rcb_list[res].state:
                                self.rcb_list[res].state -= units_need
                                delete_waitlist += [(units_need,pcb)]
                                pcb.state = 1
                                pcb.resource += [(r,n)]
                                self.rl[pcb.rank] += [pcb]
                        for i in delete_waitlist:
                            del self.rcb_list[res].waitlist[self.rcb_list[res].waitlist.index(i)]
                    self.scheduler()
                else:
                    print('-1',end = " ")
            else:
                print('-1',end = " ")
        else:
            print('-1',end = " ")



    def timeout(self):

        self.rl[self.runing_process.rank] = self.rl[self.runing_process.rank][1:]+[self.rl[self.runing_process.rank][0]]
        self.scheduler()

    def __return_highest_rank(self):
        for i in [2,1,0]:
            if self.rl[i] != []:
                for j in self.rl[i]:
                    if j.state == 1:
                        return j

    def scheduler(self):
        self.runing_process = self.__return_highest_rank()
        print(f'{self.pcb_list.index(self.runing_process)}',end = " ")



#


if __name__ == '__main__': 
    shell(sys.argv[1])