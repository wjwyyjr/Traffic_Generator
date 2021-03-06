import sys
import datetime
import argparse

parser = argparse.ArgumentParser(description='Task Graph Traffic Pattern Generator v1.0')
parser.add_argument('--file', '-f', required=True, help='The application description file.')
parser.add_argument('--check-output-file', '-c', action='store_true', help='Output a verification file.')
args = parser.parse_args()

application_model_file = args.file
if_check = args.check_output_file

#################################### Read Processor configuration ####################################
PE_num = 13
config = []
with open('PE.cfg', "r") as ProcessorConfig:
    # load the config from the line 9
    config = ProcessorConfig.readlines()[9:]

if config[0].find("Processor") != -1:
    Processor_num = int(config[1].strip("\n"))
    print("Read Processor Configure Information ! ")
    if Processor_num != PE_num:
        print("Processor Number Wrong !")
        sys.exit(-1)
else:
    print("Read Processor Configure Information Error !")
    sys.exit(-1)

# store the configuration information of PEs, Core, DDR, etc.
Processor = {}
mapping_pe_id = {}
# the current task number on a proc
Task_schedule = {}
PECfg_offset = 2
for i in range(0, Processor_num):
    # for each processor, use a dict , key is name, value is list
    Processor[config[i+PECfg_offset].split(" ")[0]] = config[i+PECfg_offset].strip("\n").split(" ")[1:]
    Task_schedule[config[i+PECfg_offset].split(" ")[0]] = -1
    mapping_pe_id[config[i+PECfg_offset].strip("\n").split(" ")[1]] = config[i+PECfg_offset].split(" ")[0]

# store the message size for each message type
Message = {}
MsgCfg_offset = PECfg_offset + Processor_num + 1
if config[MsgCfg_offset - 1].find("Message") != -1:
    MsgType_num = int(config[MsgCfg_offset].strip("\n"))
    print("Read Message Configure Information ! ")
else:
    print("Read Message Configure Information Error !")
    sys.exit(-1)

for i in range(MsgType_num):
    Message[config[i+MsgCfg_offset+1].split(" ")[0]] = config[i+MsgCfg_offset+1].strip("\n").split(" ")[1:]

###### Current Message Size ##########
Current_Msg_Size = []
for i in Message.values():
    Current_Msg_Size.append(i[0])
######################################

#################################### Read Application ####################################
model = []
with open(application_model_file, "r") as Appmodel:
    # load the model from the line 7
    model = Appmodel.readlines()[7:]
task_num = int(model[0].strip("\n"))
# store the task infomation
mapped_proc_id = []
schedule = []
task_mu = []
task_sigma = []
# store the edge information
src_task_id = []
dst_task_id = []
src_proc_id = []
dst_proc_id = []
edge_mu = []
msg_type_list = []

Model_offset = 1
i = Model_offset
task_id = 0
edge_id = 0
## Note Here !!! When to break loop should be careful ! Here we check the next two PEs, So we 
## Add the "End" in the model !
while i in range(Model_offset, Model_offset + len(model) - 3 ):
    task_info = model[i].strip("\n").split(" ")
    task_info_1 = model[i+1].strip("\n").split(" ")
    task_info_2 = model[i+2].strip("\n").split(" ")
    pe_id = task_info[0]
    msg_type = int(task_info[1])
    exec_iters = int(task_info[2])
    ######### Use DDR Push Mechanism #########
    if pe_id == "PE_0" and task_info_1[0] == "Core" and \
        task_info_2[0] == "DDR":

        ### Task
        # PE_0
        mapped_proc_id.append(Processor[pe_id][0])
        Task_schedule[pe_id] += 1
        schedule.append(Task_schedule[pe_id])
        task_mu.append(Processor[pe_id][1])
        task_sigma.append(Processor[pe_id][2])
        # Core
        pe_id_1 = task_info_1[0]
        msg_type_1 = int(task_info_1[1])
        exec_iters_1 = int(task_info_1[2])
        # DDR
        pe_id_2 = task_info_2[0]
        msg_type_2 = int(task_info_2[1])
        exec_iters_2 = int(task_info_2[2])

        ### Edge
        # PE_0 to Core
        src_task_id.append(task_id)
        dst_task_id.append(task_id + 2)
        src_proc_id.append(Processor[pe_id][0])
        dst_proc_id.append(Processor[pe_id_1][0])
        if dst_proc_id[edge_id] != Processor["Core"][0]:
            print("HQM send msg to Core Error !")
            sys.exit(0)
        edge_mu.append(Current_Msg_Size[msg_type])
        msg_type_list.append(msg_type)
        edge_id += 1
        # PE_0 to DDR
        src_task_id.append(task_id)
        dst_task_id.append(task_id + 1)
        src_proc_id.append(Processor[pe_id][0])
        dst_proc_id.append(Processor[pe_id_2][0])
        if dst_proc_id[edge_id] != Processor["DDR"][0]:
            print("HQM send msg to DDR Error !")
            sys.exit(0)
        edge_mu.append(Current_Msg_Size[msg_type])
        msg_type_list.append(msg_type)
        edge_id += 1

        task_id += 1

        if exec_iters_1 != exec_iters_2:
            print("Error! the execution times for DDR and Core is not equal ! ")
        for j in range(exec_iters_1):
            #### DDR Push to Core
            ### Task
            mapped_proc_id.append(Processor[pe_id_2][0])
            Task_schedule[pe_id_2] += 1
            schedule.append(Task_schedule[pe_id_2])
            task_mu.append(Processor[pe_id_2][1])
            task_sigma.append(Processor[pe_id_2][2])

            ### Edge
            src_task_id.append(task_id)
            dst_task_id.append(task_id + 1)
            src_proc_id.append(Processor[pe_id_2][0])
            dst_proc_id.append(Processor[pe_id_1][0])
            if dst_proc_id[edge_id] != Processor["Core"][0]:
                print("DDR prefetch msg to Core Error !")
                sys.exit(0)
            edge_mu.append(Current_Msg_Size[msg_type_2])
            msg_type_list.append(msg_type_2)
            edge_id += 1

            task_id += 1

            #### Core to DDR
            ### Task
            mapped_proc_id.append(Processor[pe_id_1][0])
            Task_schedule[pe_id_1] += 1
            schedule.append(Task_schedule[pe_id_1])
            task_mu.append(Processor[pe_id_1][1])
            task_sigma.append(Processor[pe_id_1][2])

            ### Edge
            src_task_id.append(task_id)
            dst_task_id.append(task_id + 1)
            src_proc_id.append(Processor[pe_id_1][0])
            dst_proc_id.append(Processor[pe_id_2][0])
            if dst_proc_id[edge_id] != Processor["DDR"][0]:
                print("Core send msg to DDR Error !")
                sys.exit(0)
            edge_mu.append(Current_Msg_Size[msg_type_1])
            msg_type_list.append(msg_type_1)
            edge_id += 1

            task_id += 1
        
        #### Due to DDR Push, We need extra task for DDR receives the ack signal
        mapped_proc_id.append(Processor[pe_id_2][0])
        Task_schedule[pe_id_2] += 1
        schedule.append(Task_schedule[pe_id_2])
        task_mu.append(Processor[pe_id_2][1])
        task_sigma.append(Processor[pe_id_2][2])

        task_id += 1

        i += 3
    ######### Use the SQM #########
    elif pe_id == "Core" and task_info_1[0].find("PE") != -1 and \
        task_info_2[0] == "DDR":

        ### Task
        # Core
        mapped_proc_id.append(Processor[pe_id][0])
        Task_schedule[pe_id] += 1
        schedule.append(Task_schedule[pe_id])
        task_mu.append(Processor[pe_id][1])
        task_sigma.append(Processor[pe_id][2])
        # PE
        pe_id_1 = task_info_1[0]
        msg_type_1 = int(task_info_1[1])
        exec_iters_1 = int(task_info_1[2])
        # DDR
        pe_id_2 = task_info_2[0]
        msg_type_2 = int(task_info_2[1])
        exec_iters_2 = int(task_info_2[2])

        ### Edge
        # Core to PE
        src_task_id.append(task_id)
        dst_task_id.append(task_id + 1)
        src_proc_id.append(Processor[pe_id][0])
        dst_proc_id.append(Processor[pe_id_1][0])
        if src_proc_id[edge_id] != Processor["Core"][0]:
            print("Core send msg to PE (SQM) Error !")
            sys.exit(1)
        edge_mu.append(Current_Msg_Size[msg_type])
        msg_type_list.append(msg_type)
        edge_id += 1        
        # Core to DDR
        src_task_id.append(task_id)
        dst_task_id.append(task_id + 2)
        src_proc_id.append(Processor[pe_id][0])
        dst_proc_id.append(Processor[pe_id_2][0])
        if dst_proc_id[edge_id] != Processor["DDR"][0]:
            print("Core send msg to DDR (SQM) Error !")
            sys.exit(1)
        edge_mu.append(Current_Msg_Size[msg_type])
        msg_type_list.append(msg_type)
        edge_id += 1     

        task_id += 1

        if exec_iters_1 != exec_iters_2:
            print("Error! the execution times for DDR and Core is not equal ! ")
        for j in range(exec_iters_1):
            #### PE Get Data from DDR
            ### Task
            mapped_proc_id.append(Processor[pe_id_1][0])
            Task_schedule[pe_id_1] += 1
            schedule.append(Task_schedule[pe_id_1])
            task_mu.append(Processor[pe_id_1][1])
            task_sigma.append(Processor[pe_id_1][2])

            ### Edge
            src_task_id.append(task_id)
            dst_task_id.append(task_id + 1)
            src_proc_id.append(Processor[pe_id_1][0])
            dst_proc_id.append(Processor[pe_id_2][0])
            if dst_proc_id[edge_id] != Processor["DDR"][0]:
                print("PE send msg to DDR (SQM) Error !")
                sys.exit(1)
            edge_mu.append(Current_Msg_Size[msg_type_1])
            msg_type_list.append(msg_type_1)
            edge_id += 1

            task_id += 1

            #### DDR Send Data to PE
            ### Task
            mapped_proc_id.append(Processor[pe_id_2][0])
            Task_schedule[pe_id_2] += 1
            schedule.append(Task_schedule[pe_id_2])
            task_mu.append(Processor[pe_id_2][1])
            task_sigma.append(Processor[pe_id_2][2])

            ### Edge
            src_task_id.append(task_id)
            dst_task_id.append(task_id + 1)
            src_proc_id.append(Processor[pe_id_2][0])
            dst_proc_id.append(Processor[pe_id_1][0])
            if src_proc_id[edge_id] != Processor["DDR"][0]:
                print("DDR send msg to PE (SQM) Error !")
                sys.exit(1)
            edge_mu.append(Current_Msg_Size[msg_type_2])
            msg_type_list.append(msg_type_2)
            edge_id += 1            
            
            task_id += 1

        i += 3
    ######### Other Situation #########
    else:
        pe_id_1 = task_info_1[0]
        msg_type_1 = int(task_info_1[1])
        exec_iters_1 = int(task_info_1[2])
        #### Iterations larger than 1
        if exec_iters > 1:
            if exec_iters != exec_iters_1:
                print("Error! the execution times is not equal ! ")
                sys.exit(2)
            for j in range(exec_iters):
                #### The Current PE to Next PE
                ### Task
                mapped_proc_id.append(Processor[pe_id][0])
                Task_schedule[pe_id] += 1
                schedule.append(Task_schedule[pe_id])
                task_mu.append(Processor[pe_id][1])
                task_sigma.append(Processor[pe_id][2])

                #### Edge
                src_task_id.append(task_id)
                dst_task_id.append(task_id + 1)
                src_proc_id.append(Processor[pe_id][0])
                dst_proc_id.append(Processor[pe_id_1][0])
                if dst_proc_id[edge_id] != Processor[pe_id_1][0]:
                    print(pe_id+" send msg to "+pe_id_1+" Error !")
                    sys.exit(0)
                edge_mu.append(Current_Msg_Size[msg_type])
                msg_type_list.append(msg_type)
                edge_id += 1

                task_id += 1

                #### The Next PE to Current PE
                ### Task
                mapped_proc_id.append(Processor[pe_id_1][0])
                Task_schedule[pe_id_1] += 1
                schedule.append(Task_schedule[pe_id_1])
                task_mu.append(Processor[pe_id_1][1])
                task_sigma.append(Processor[pe_id_1][2])

                ### Edge            
                src_task_id.append(task_id)
                dst_task_id.append(task_id + 1)
                src_proc_id.append(Processor[pe_id_1][0])
                dst_proc_id.append(Processor[pe_id][0])
                if dst_proc_id[edge_id] != Processor[pe_id][0]:
                    print(pe_id_1+" send msg to "+pe_id+" Error !")
                    sys.exit(0)
                edge_mu.append(Current_Msg_Size[msg_type_1])
                msg_type_list.append(msg_type_1)
                edge_id += 1

                task_id += 1

            i += 2
        #### iterations equal to 1
        else:
            #### Just the Current PE to Next PE
            ### Task
            mapped_proc_id.append(Processor[pe_id][0])
            Task_schedule[pe_id] += 1
            schedule.append(Task_schedule[pe_id])
            task_mu.append(Processor[pe_id][1])
            task_sigma.append(Processor[pe_id][2])

            #### Edge
            src_task_id.append(task_id)
            dst_task_id.append(task_id + 1)
            src_proc_id.append(Processor[pe_id][0])
            dst_proc_id.append(Processor[pe_id_1][0])
            if dst_proc_id[edge_id] != Processor[pe_id_1][0]:
                print(pe_id+" send msg to "+pe_id_1+" Error !")
                sys.exit(0)
            edge_mu.append(Current_Msg_Size[msg_type])
            msg_type_list.append(msg_type)
            edge_id += 1

            task_id += 1

            ### Note !! For the last Task
            if i == Model_offset + len(model) - 4:
                mapped_proc_id.append(Processor[pe_id_1][0])
                Task_schedule[pe_id_1] += 1
                schedule.append(Task_schedule[pe_id_1])
                task_mu.append(Processor[pe_id_1][1])
                task_sigma.append(Processor[pe_id_1][2])

                task_id += 1

                if model[i+2] != "End":
                    print("Wrong End !")
                    sys.exit(-2)                

            i += 1

#################################### Output Task Graph Description File ####################################
outputFileName = "../traffic/" + application_model_file.replace(".info", ".stp")
# outputFileName = application_model_file.replace(".info", ".stp")
with open(outputFileName, "w") as of:
    of.writelines("/********************************************************\n")
    of.writelines("*\n")
    of.writelines("* File Name:      \t"+outputFileName+"\n")
    of.writelines("* Tool:           \t"+"Task Graph Traffic Pattern Generator"+"\n")
    of.writelines("* Creation Time:  \t"+datetime.datetime.now().strftime("%Y-%m-%d %H:%M")+"\n")
    of.writelines("* Number of Tasks:\t"+str(task_id)+"\n")
    of.writelines("* Number of Edges:\t"+str(edge_id)+"\n")
    for i in range(7):
        of.writelines("*\n")
    of.writelines("********************************************************/\n")

    # write first line
    of.writelines("0"+"\t"+str(PE_num)+"\t"+str(task_id)+"\t"+str(edge_id)+"\n")

    # write task
    for i in range(task_id):
        of.writelines(str(i)+"\t"+mapped_proc_id[i]+"\t"+str(schedule[i])+"\t"+task_mu[i]+"\t"+task_sigma[i]+"\n")

    # write edge
    for i in range(edge_id):
        of.writelines(str(i)+"\t"+str(src_task_id[i])+"\t"+str(dst_task_id[i])+"\t"+src_proc_id[i]+"\t"+dst_proc_id[i]\
            +"\t"+"0\t2\t0\t2\t"+edge_mu[i]+"\t0"+"\t0.1"+"\n")

#################################### Output Task Graph Verfication File ####################################
if if_check:
    outputVerificationFile = "../verify/" + application_model_file.replace(".info", ".graph")
    # outputVerificationFile = application_model_file.replace(".info", ".graph")
    with open(outputVerificationFile, "w") as verif_f:
        verif_f.writelines("/********************************************************\n")
        verif_f.writelines("*\n")
        verif_f.writelines("* File Name:      \t"+outputVerificationFile+"\n")
        verif_f.writelines("* Tool:           \t"+"Task Graph Traffic Pattern Generator"+"\n")
        verif_f.writelines("* Creation Time:  \t"+datetime.datetime.now().strftime("%Y-%m-%d %H:%M")+"\n")
        verif_f.writelines("* Number verif_f Tasks:\t"+str(task_id)+"\n")
        verif_f.writelines("* Number verif_f Edges:\t"+str(edge_id)+"\n")
        verif_f.writelines("*\n")
        verif_f.writelines("********************************************************/\n")

        i = 0
        while i in range(edge_id - 1):
            ### Two Continuous Edges with same src_proc_id
            if src_proc_id[i] == src_proc_id[i+1]:
                ## The two dst_proc_id have edges
                if set([dst_proc_id[i], dst_proc_id[i+1]]) == set([src_proc_id[i+2], dst_proc_id[i+2]]):
                    verif_f.writelines(mapping_pe_id[src_proc_id[i]]+"\n")
                    verif_f.writelines("| \\\n")
                    verif_f.writelines("|  "+mapping_pe_id[src_proc_id[i+2]]+"\n")
                    verif_f.writelines("| /\n")
                    verif_f.writelines(mapping_pe_id[dst_proc_id[i+2]]+"\n")
                    if dst_proc_id[i+2] == src_proc_id[i+3]:
                        verif_f.writelines("|\n")
                    i += 4
                ## The two dst_proc_id not have edges like a tree
                elif src_proc_id[i+2] == src_proc_id[i]:
                    verif_f.writelines("|  "+mapping_pe_id[dst_proc_id[i]]+"\n")
                    verif_f.writelines("| /\n")
                    i += 1
                else:
                    verif_f.writelines(mapping_pe_id[src_proc_id[i]]+"\n")
                    if dst_proc_id[i] == src_proc_id[i+2]:
                        a = i + 1
                        b = i
                    else:
                        a = i
                        b = i + 1
                    verif_f.writelines("|"+" \\\n")
                    verif_f.writelines("|  "+mapping_pe_id[dst_proc_id[a]]+"\n")
                    verif_f.writelines("|\n")
                    verif_f.writelines(mapping_pe_id[dst_proc_id[b]]+"\n")
                    if dst_proc_id[b] == src_proc_id[i+2]:
                        verif_f.writelines("|\n")
                    i += 3
            ### The General Flow
            elif dst_proc_id[i] == src_proc_id[i+1]:
                ## For the End
                if i == edge_id - 2:
                    verif_f.writelines(mapping_pe_id[src_proc_id[i]]+"\n")
                    verif_f.writelines("|\n")
                    verif_f.writelines(mapping_pe_id[dst_proc_id[i]]+"\n")
                    verif_f.writelines("|\n")
                    verif_f.writelines(mapping_pe_id[dst_proc_id[i+1]]+"\n")
                else:
                    verif_f.writelines(mapping_pe_id[src_proc_id[i]]+"\n")
                    verif_f.writelines("|\n")
                i += 1
            else:
                print("No Matches ! Error !")
                sys.exit(-1)          

        color = {}
        w = '\033[0m'
        color[0] = '\033[0m'     # default msg type 0
        color[1] = '\033[31m'    # red     msg type 1
        color[2] = '\033[32m'    # green   msg type 2
        i = 0
        while i in range(edge_id - 1):
            ### Two Continuous Edges with same src_proc_id
            if src_proc_id[i] == src_proc_id[i+1]:
                ## The two dst_proc_id have edges
                if set([dst_proc_id[i], dst_proc_id[i+1]]) == set([src_proc_id[i+2], dst_proc_id[i+2]]):
                    ## a is for searching the second edge
                    if dst_proc_id[i+2] ==  dst_proc_id[i]:
                        a = i + 1
                    else:
                        a = i
                    print(mapping_pe_id[src_proc_id[i]])
                    print(color[msg_type_list[i]]+"|"+color[msg_type_list[a]]+" \\"+w)
                    print(color[msg_type_list[i]]+"|  "+w+mapping_pe_id[src_proc_id[i+2]])
                    print(color[msg_type_list[i]]+"|"+w+color[msg_type_list[i+2]]+" /"+w)
                    print(mapping_pe_id[dst_proc_id[i+2]])
                    if dst_proc_id[i+2] == src_proc_id[i+3]:
                        print(color[msg_type_list[i+3]]+"|"+w)
                    i += 4
                elif src_proc_id[i+2] == src_proc_id[i]:
                    print(color[msg_type_list[i-1]]+"|  "+w+mapping_pe_id[dst_proc_id[i]])
                    print(color[msg_type_list[i-1]]+"|"+color[msg_type_list[i]]+" /"+w)
                    i += 1
                ## The two dst_proc_id not have edges like a tree
                else:
                    print(mapping_pe_id[src_proc_id[i]])
                    if dst_proc_id[i] == src_proc_id[i+2]:
                        a = i + 1
                        b = i
                    else:
                        a = i
                        b = i + 1
                    print(color[msg_type_list[b]]+"|"+color[msg_type_list[b]]+" \\"+w)
                    print(color[msg_type_list[b]]+"|  "+w+mapping_pe_id[dst_proc_id[a]])
                    print(color[msg_type_list[b]]+"|"+w)
                    print(mapping_pe_id[dst_proc_id[b]])
                    if dst_proc_id[b] == src_proc_id[i+2]:
                        print(color[msg_type_list[i+2]]+"|"+w)
                    i += 3
            ### The General Flow
            elif dst_proc_id[i] == src_proc_id[i+1]:
                ## For the End
                if i == edge_id - 2:
                    print(mapping_pe_id[src_proc_id[i]])
                    print(color[msg_type_list[i]]+"|"+w)
                    print(mapping_pe_id[dst_proc_id[i]])
                    print(color[msg_type_list[i+1]]+"|"+w)
                    print(mapping_pe_id[dst_proc_id[i+1]])
                else:
                    print(mapping_pe_id[src_proc_id[i]])
                    print(color[msg_type_list[i]]+"|"+w)
                i += 1
            else:
                print("No Matches ! Error !")
