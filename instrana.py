
"""
测试用例：
【已经修改】
0. 选择数据库 默认是hei
use hei
1. 创建数据库
create database hei

2. 创建表course：
create table course(cid int, cname varchar, ctime int, primary key(cid))

3. 创建表student：
create table student(sid int, sname varchar, age int, primary key(sid))

4. 显示元数据
show meta data

5. 显示数据库
show databases

6. 显示表
show tables

7. select投影：
select * from student

8. select投影2
select sid, age from student

9. select where查询
select sname,age from student where age=18

10. 删除数据库
drop database db

11. 删除表
use database db
drop table tb

12. 删除表项 
use database db
delete from table where condition

3.2 给course增加表项：
insert into course values(2,test,2022)

3.3 给course增加表项(插入值多于表的属性)：
insert into course values(2,test,2022,20)
"error:too many values"

4.1. 给course增加表项(由于外键约束出错)：
insert into course values(1,test,2022)

4.2. 给student增加表项：
insert into student values(3,zhy,4,5)

4.3. 给student增加表项（由于主键约束出错）：
insert into student values(1,zhy,4,5)

7. 修改表项：
update student set age=5 where sname=wyj

8.修改表项(属性不存在或者没找到对应表项):
update student set age=5 where name=wyj
update student set age=5 where sname=dddddd
"Error: wrong key."
"""

import pandas as pd
import os
import time
import re
from MemoryManager import MemoryManager

BASE_PATH = os.getcwd()
# 数据库信息保存
DB_META_DATA_PATH = os.path.join(r".\meta_data\database_meta_data1.csv")
# 表信息保存
TB_META_DATA_PATH = os.path.join(r".\meta_data\table_meta_data1.csv")
DEFAULT_DB_NAME = "hei"
mmManager = MemoryManager("system")

# 显示所有列
pd.set_option('display.max_columns', None)
# 显示所有行
pd.set_option('display.max_rows', None)

# 选择数据库
use_dbs_instr = r"use\b\s[a-zA-Z0-9_]+"
# insert语句
insert_instr="insert\\b\\sinto\\b\\s[a-zA-Z0-9_]+\\b\\svalues\((([0-9]*)|([a-zA-Z0-9_]*))?(\,([0-9]*)|([a-zA-Z0-9_]*))*\)"
# update语句
update_instr="update\\b\\s[a-zA-Z0-9_]+\\b\\sset\\b\\s[a-zA-Z0-9_]+[>=<][a-zA-Z0-9_]+\\b\\swhere\\b\\s[a-zA-Z0-9_]+[>=<][a-zA-Z0-9_]+"
# 删除数据库
drop_database_instr = r"drop\b\sdatabase\b\s[a-zA-Z0-9_]+"
# 删除表
drop_table_instr = r"drop\b\stable\b\s[a-zA-Z0-9_]+"
# 删除表项
delete_where_table_instr = r"delete\b\sfrom\b\s[a-zA-Z0-9_]+\b\swhere\b\s[a-zA-Z0-9_]+[>=<][a-zA-Z0-9_]+"
# 查询
select_table_instr = r"(select\b\s([a-zA-Z0-9_]+,)*[a-zA-Z0-9_]+\b\sfrom\b\s[a-zA-Z0-9_]+)"
select_where_table_instr = r"select\b\s([a-zA-Z0-9_]+,)*[a-zA-Z0-9_]+\b\sfrom\b\s[a-zA-Z0-9_]+\b\swhere\b\s[a-zA-Z0-9_]+[>=<][0-9]+"

type_list = ["varchar", "int", "null"]


# 初始化数据库信息表
def init_databases_table():
    try:
        db_meta_data_pd = pd.read_csv(DB_META_DATA_PATH)
    except FileNotFoundError:
        # 包含数据库id，数据库名，创建时间，数据库是否有效的标记
        db_meta_data_columns = ["db_id", "db_name", "create_time", "invalid"]
        db_meta_data_pd = pd.DataFrame(columns=db_meta_data_columns,index=[0])
        db_meta_data_pd.to_csv(DB_META_DATA_PATH, index=False, sep=",")


# 初始化二维表信息表
def init_meta_data():
    try:
        tb_meta_data_pd = pd.read_csv(TB_META_DATA_PATH)
    except FileNotFoundError:
        # 包含数据库id，表id，表名，属性列表，属性类型列表，主键，外键，行数，表大小，修改时间，创建时间，用户id，组id和表是否有效的标记
        tb_meta_data_columns = ["db_id", "table_id", "table_name", "column_list",
                                "type_list", "primary_key","foreign_key",
                                "row_num", "size_in_byte", "modify_time", 
                                "create_time", "uid", "gid", "invalid"]
        tb_meta_data_pd = pd.DataFrame(columns=tb_meta_data_columns,index=[0])
        tb_meta_data_pd.to_csv(TB_META_DATA_PATH, index=False, sep=",")

# 初始化索引表
def init_index_table(path):
    try:
        ib_meta_data_pd = pd.read_csv(path)
    except FileNotFoundError:
        # 包含有序主键和行数
        ib_meta_data_columns = ["primkey_val", "row_number"]
        ib_meta_data_pd = pd.DataFrame(columns=ib_meta_data_columns)
        ib_meta_data_pd.to_csv(path, index=False, sep=",")

# 选择数据库
def analyse_use_db(instr):
    _, db_name = instr.split(" ")
    db_meta_data_df = pd.read_csv(DB_META_DATA_PATH)
    invalid = db_meta_data_df[db_meta_data_df["db_name"] == db_name]["invalid"].values.tolist()[0]
    if db_name not in db_meta_data_df["db_name"].values or invalid == True:
        print("Error: database `", db_name, "` not exist! ")
        exit()
    print("Current database:", db_name)
    return db_name

# 二分查找
def binsearch(table_df,attrv,attr):
    lst = list(table_df[:][attr].values)
    l = 0;r = table_df.shape[0]
    while(l<r):
        mid = int((l+r)/2)
        if lst[mid] == attrv:
            return mid
        elif lst[mid] > attrv:
            right = mid
        else:
            left = mid
        mid = int((right + left)/2)
    else:
        return -1

# 指令函数
def create_database(tokens,):
    temp_dbmeta = pd.read_csv(DB_META_DATA_PATH)
    # loc通过行索引中的具体值来取行数据,这里判断第一行是否有内容
    if pd.isnull(temp_dbmeta.loc[0, "db_id"]):
        db_id = 0
    else:
        db_id = temp_dbmeta.shape[0]
    # 数据库名在第三个词的位置：create database xxx
    new_db_name = tokens[2]
    if not os.path.exists(new_db_name):
        # 数据库以文件夹形式存储，下存一些二维表
        os.mkdir(new_db_name)
        print("Create database", new_db_name, "successfully!")
    else:
        # 数据库已存在错误
        print("Error: This database is already existing! ")
        exit()
    
    db_stat = os.stat(new_db_name)
    # 添加数据库信息
    temp_dbmeta.loc[db_id, "db_id"] = db_id
    temp_dbmeta.loc[db_id, "db_name"] = new_db_name
    temp_dbmeta.loc[db_id, "create_time"] = time.ctime(db_stat.st_ctime) # 文件创建时间
    temp_dbmeta.loc[db_id, "invalid"] = False
    temp_dbmeta.to_csv(DB_META_DATA_PATH, index=False, sep=",") # 不保留行索引且用逗号分割

def show_database():
    # 读取数据库信息表，输出所有数据库的信息
    temp_dbmeta = pd.read_csv(DB_META_DATA_PATH)
    db_name_list = temp_dbmeta[temp_dbmeta["invalid"] == False]["db_name"].values # 得到所有有效的信息
    for db_name in db_name_list:
        print("database name: {} ".format(db_name))

def create_table(tokens,dbname,db_path):
    # 读取数据库信息表并获得所属数据库id
    temp_dbmeta = pd.read_csv(DB_META_DATA_PATH)
    db_id = int(temp_dbmeta[temp_dbmeta["db_name"] == dbname]["db_id"].values[0])
    # 读取二维表的信息表并为新表分配id
    temp_table_meta = pd.read_csv(TB_META_DATA_PATH)
    # 判断信息表是否为空
    if pd.isnull(temp_table_meta.loc[0, "table_id"]):
        table_id = 0
    else:
        table_id = temp_table_meta.shape[0]
    # 表名在第三个词的位置：create table xxx
    new_table_name = tokens[2]
    temp_df = temp_table_meta[temp_table_meta["invalid"] == False]
    tb_name_list = temp_df[temp_df["db_id"] == db_id]["table_name"].values
    # 判断表名是否重复
    if new_table_name in tb_name_list:
        print("Error: This table", new_table_name, "is already existing! ")
        exit()
    # 获取新表的属性以及数据类型
    col_tokens = [] # 属性和类型list
    # 到primary为止
    if "primary" in tokens:
        col_tokens = tokens[4:tokens.index("primary")-1]
    else:
        col_tokens = tokens[4:-1]
    # 属性list
    col_name_list = col_tokens[::3]
    # 数据类型list
    col_type_list = col_tokens[1::3]
    # 判断属性和类型数目是否相同
    if len(col_name_list) != len(col_type_list):
        print("Error: Type error.")
        exit()
    # 判断类型必须是已有的类型
    for i in col_type_list:
        if i not in type_list:
            print("Error: type error.")
            exit()
    # 设置主键
    primkey = ""
    if "primary" in tokens:
        primkey = tokens[tokens.index("primary")+3]
        if primkey not in col_name_list:
            print("Error: primary key error.")
            exit()
    # 设置外键
    forekey = "null"
    fk_source = ""
    if "foreign" in tokens:
        # 设置的外键
        forekey = tokens[tokens.index("foreign")+3]    
        # 找到references
        if "references" in tokens:
            fk_source = tokens[tokens.index("references")+1] # 外键所在的表
            fk_val = tokens[tokens.index("references")+3] # 外键值
            # 设置的外键矛盾，报错
            if forekey != fk_val:
                print("Error: foreign key error.")
                exit()
        # 没有references则报错
        else:
            print("Error: foreign key error.")
            exit()
        temp_df = temp_table_meta[temp_table_meta["invalid"] == False]
        # 提取外键所在的表的列
        tb_fk_source = temp_df[temp_df["table_name"] == fk_source].values
        print(tb_fk_source)
        # 没有references的表，报错
        if fk_val not in tb_fk_source:
            print("Error: foreign key error.")
            exit()
        else:
            # 找到该属性对应的数据类型，push进list中
            fk_type = temp_df[temp_df["table_name"] == fk_source]["type_list"].values.tolist()[0]
            print(fk_type)

            col_name_list.append(forekey)
            col_type_list.append(fk_type)

    # 新增表
    new_table_df = pd.DataFrame(columns=col_name_list)
    new_table_path = os.path.join(db_path, new_table_name + ".csv")
    # 新建索引表
    new_table_indexpath = os.path.join(db_path, new_table_name + "_index.csv")
    init_index_table(new_table_indexpath)

    new_table_df.to_csv(new_table_path, index=False, sep=',')
    print("create table", new_table_name, "successfully!")
    table_stat = os.stat(new_table_path)
    # 更新表信息
    join_str = ' '
    column_name_str = join_str.join(col_name_list) # 多个列用空格分隔，只用一个字符串表示
    column_type_str = join_str.join(col_type_list)
    
    temp_table_meta.loc[table_id, 'db_id'] = db_id
    temp_table_meta.loc[table_id, 'table_id'] = table_id
    temp_table_meta.loc[table_id, 'table_name'] = new_table_name
    temp_table_meta.loc[table_id, 'column_list'] = column_name_str
    temp_table_meta.loc[table_id, 'type_list'] = column_type_str
    temp_table_meta.loc[table_id, 'primary_key'] = primkey
    temp_table_meta.loc[table_id, 'foreign_key'] = forekey
    temp_table_meta.loc[table_id, 'row_num'] = 0
    temp_table_meta.loc[table_id, 'size_in_byte'] = table_stat.st_size
    temp_table_meta.loc[table_id, 'modify_time'] = time.ctime(table_stat.st_mtime)
    temp_table_meta.loc[table_id, 'create_time'] = time.ctime(table_stat.st_ctime)
    temp_table_meta.loc[table_id, 'uid'] = table_stat.st_uid
    temp_table_meta.loc[table_id, 'gid'] = table_stat.st_gid
    temp_table_meta.loc[table_id, 'invalid'] = False
    temp_table_meta.to_csv(TB_META_DATA_PATH, index=False, sep=',')

def insert_data(instr,db_path):
    # 指令格式：insert into <table_name> values(a,b,c...) 
    # 分割
    tokens=[i for i in re.split(r"([ ,();=])", instr.lower().strip()) if i not in[' ',',',')','(','']]
    table_name = tokens[2] # 第三位是表名
    idx = tokens.index("values")

    table_path = os.path.join(db_path, table_name + ".csv")
    # 先判断表是否存在，存在则找到这个表
    try:
        temp_table = pd.read_csv(table_path)
        temp_table_meta = pd.read_csv(TB_META_DATA_PATH)
        # print(temp_table_meta[temp_table_meta["table_name"] == table_name].index.tolist())
        index = temp_table_meta[temp_table_meta["table_name"] == table_name].index.tolist()[0] # 该表在meta中的索引
    except FileNotFoundError:
        print("Error: File Not Found.")
        exit()
    
    # 属性数量
    table_num = temp_table.shape[1]
    
    insert_num=len(tokens)-idx-1
    # 插入值过多
    if insert_num>table_num: 
        print("Error: num of value error.")
        exit()

    # 保存从token中提取到的数据
    newdatalst = {} 
    for column in temp_table.columns:
        idx+=1
        newdatalst[column] = tokens[idx]
    temp_table.loc[temp_table.shape[0]] = list(newdatalst.values())
    # temp_table.loc[table_num] = list(newdatalst.values())

    # # 判断外键约束
    # forekey = str(temp_table_meta.loc[index, "foreign_key"])
    # if forekey == "null":
    #     pass
    # elif forekey.count(" ") == 1:
    #     source_table, fk_val = forekey.split(" ")
    #     try:
    #         rtable_path = os.path.join(db_path, source_table + ".csv")
    #         sourcetable_df = pd.read_csv(rtable_path)
    #     except FileNotFoundError:
    #         print("Error: File Not Found.")
    #         exit()
    #     if newdatalst[fk_val] not in [str(i) for i in list(sourcetable_df.loc[:, fk_val])]:
    #         print("Error: Foreign key constraint error.")
    #         exit()


    # 判断主键约束
    primkey = str(temp_table_meta.loc[index, "primary_key"])
    if newdatalst[primkey] in [str(i) for i in list(temp_table.loc[:, primkey][: -1])]:
        print("Error: primkey constraint error.")
        exit()
    
    # 添加到索引表
    new_index = [newdatalst[primkey],temp_table.shape[0]]
    indextable_path = os.path.join(db_path, table_name + "_index.csv")
    temp_table_index = pd.read_csv(indextable_path)
    column_lst = str(temp_table_meta.loc[index,"column_list"]).split(' ')
    type_lst = str(temp_table_meta.loc[index,"type_list"]).split(' ')
    for i in range(len(column_lst)):
        if(primkey == column_lst[i]):
            primtype =  type_lst[i]
            break
    # 对索引进行插入排序
    indexlen = temp_table_index.shape[0]
    point = -1
    if(primtype == 'int'):
        tmpprim = int(newdatalst[primkey] )
    for i in range(0,indexlen):
        
        if tmpprim < temp_table_index[:]['primkey_val'][i]:
            tmp = temp_table_index.loc[i]
            temp_table_index.loc[i] = new_index
            print(tmp)
            print(temp_table_index.loc[i])

            point = i
            break
        else:
            continue
    if(point == -1):
        temp_table_index.loc[indexlen] = new_index
    else:
        for i in range(point+1,indexlen):
            tmp1 = tmp
            tmp = temp_table_index.loc[i]
            temp_table_index.loc[i] = tmp1
        temp_table_index.loc[indexlen] = tmp
    
    temp_table_index.to_csv(indextable_path, index=False, sep=',')
    temp_table.to_csv(table_path, index=False, sep=',')
    stat = os.stat(table_path)

    temp_table_meta.loc[index, "row_num"] += 1
    temp_table_meta.loc[index, "modify_time"] = time.ctime(stat.st_mtime)
    temp_table_meta.loc[index, "size_in_byte"] = stat.st_size
    temp_table_meta.to_csv(TB_META_DATA_PATH, index=False, sep=',')

    # 内存管理
    mmManager.addMomeryBlock(list(newdatalst.values()),8)

    print("Insert successfully!")

def show_table(dbname):
    db_meta_data_df = pd.read_csv(DB_META_DATA_PATH)
    db_id = int(db_meta_data_df[db_meta_data_df["db_name"] == dbname]["db_id"].values[0])
    tb_meta_data_df = pd.read_csv(TB_META_DATA_PATH)
    temp_df = tb_meta_data_df[tb_meta_data_df["is_del"] == False]
    tb_name_list = temp_df[temp_df["db_id"] == db_id]["table_name"].values
    for tb_name in tb_name_list:
        print(tb_name)


def update(instr,db_path):
    # update Person set FirstName=a where LastName=b 
    tokens=[i for i in re.split(r"([ ,();=])", instr.lower().strip()) if i not in[' ',',',')','(','','=']]
    table_name=tokens[1]

    table_path = os.path.join(db_path, table_name + ".csv")
    try:
        table_df = pd.read_csv(table_path)
        meta_data_df = pd.read_csv(TB_META_DATA_PATH)
        index_m = meta_data_df[meta_data_df["table_name"] == table_name].index.tolist()[0]
    except FileNotFoundError:
        print("Error: file not found.")
        exit()
    attr=tokens[-2]#where后的索引name
    attrv=tokens[-1]#attr的值
    change_item=tokens[3]#修改表项name
    newv=tokens[4]#修改值
    try:
        table_df[change_item]=table_df[change_item].astype('str')
        table_df[attr]=table_df[attr].astype('str')
        # 修改，索引和非索引
        indextable_path = os.path.join(db_path, table_name + "_index.csv")
        temp_table_index = pd.read_csv(indextable_path)
        primkey = str(meta_data_df.loc[index_m, "primary_key"])
        if(attr == primkey):
            idx1 = binsearch(temp_table_index ,attrv,attr)
            if(idx1 == -1):
                exit()
        else:
            if(len(table_df.loc[table_df[attr]==attrv,change_item].index)==0):
                exit()
        # if(len(table_df.loc[table_df[attr]==attrv,change_item].index)==0):
        #     exit()

        table_df.loc[table_df[attr]==attrv,change_item]=newv
    except :
        print("Error: wrong key.")
        exit()
    table_df.to_csv(table_path, index=False, sep=',')
    stat = os.stat(table_path)
    meta_data_df.loc[index_m, "row_num"] += 1
    meta_data_df.loc[index_m, "modify_time"] = time.ctime(stat.st_mtime)
    meta_data_df.loc[index_m, "size_in_byte"] = stat.st_size
    meta_data_df.to_csv(TB_META_DATA_PATH, index=False, sep=',')
    print("update successfully!")

def select_all(instr,db_path):
    tokens = re.split(r"([ ,();=])", instr.lower().strip())
    tokens = [t for t in tokens if t not in [' ', '', '\n']]
    table_name= tokens[3]
    try:
        table_path = os.path.join(db_path, table_name + ".csv")
        table_df = pd.read_csv(table_path)
    except FileNotFoundError:
        print("Error: file not found.")
        exit()
    print(table_df) 

def select_table(instr,dbpath):
    _, attr, _, table_name = instr.split(" ")
    attr_list = attr.split(",")
    try:
        table_path = os.path.join(dbpath, table_name + ".csv")
        table_df = pd.read_csv(table_path)
    except FileNotFoundError:
        print("Error: file not found.")
        exit()
    print(table_df.loc[:, attr_list])

def select_where_table(instr,dbpath):
    t1 = int(round(time.time() * 1000))
    _, attr, _, table_name, _, condition = instr.split(" ")
    attr_list = attr.split(",")
    if condition.find("<") != -1:
        condition_list = condition.split("<")
        condition_list.append("<")
    elif condition.find(">") != -1:
        condition_list = condition.split(">")
        condition_list.append(">")
    elif condition.find("=") != -1:
        condition_list = condition.split("=")
        condition_list.append("=")
    try:
        table_df = pd.read_csv(os.path.join(dbpath, table_name + ".csv")) 
        meta_data_df = pd.read_csv(TB_META_DATA_PATH)
        index_m = meta_data_df[meta_data_df["table_name"] == table_name].index.tolist()[0]
    except FileNotFoundError:
        print("Error: file not found.")
        exit()
    t2 = int(round(time.time() * 1000))
    if condition_list[-1] == "=":
        # 修改，索引和非索引
        indextable_path = os.path.join(dbpath, table_name + "_index.csv")
        temp_table_index = pd.read_csv(indextable_path)
        primkey = str(meta_data_df.loc[index_m, "primary_key"])
        if(condition_list[0] == primkey):
            idx1 = binsearch(temp_table_index ,condition_list[0],condition_list[1])
            ans = table_df[idx1]
        else:
            ans = table_df[table_df[condition_list[0]] == int(condition_list[1])]
            
        # ans = table_df[table_df[condition_list[0]] == int(condition_list[1])]
    elif condition_list[-1] == ">":
        ans = table_df[table_df[condition_list[0]] > int(condition_list[1])]
    elif condition_list[-1] == "<":
        ans = table_df[table_df[condition_list[0]] < int(condition_list[1])]
    t3 = int(round(time.time() * 1000))
    if attr == "all":
        print(ans)
    else:
        print(ans.loc[:, attr_list])
    t4 = int(round(time.time() * 1000))
    print("读取文件时间(ms)：", t2 - t1)
    print("查找时间(ms)：", t3 - t2)
    print("打印结果时间(ms)：", t4 - t3)
    print("总时间(ms)：", t4 - t1)

def dropdatabase(instr):
    _, _, db = instr.split(" ")
    db_table_temp = pd.read_csv(DB_META_DATA_PATH)
    # 从数据库表文件中查看是否有这个名称对应的并且其删除标记为FALSE的元组
    try:
        index = db_table_temp[(db_table_temp["db_name"] == db) \
        & (db_table_temp["is_del"] == False)].index.tolist()[0]
    except:
        # 如果没有，要删除的数据库不存在
        print("Error: 没有" + db + "数据库！")
        exit()
    # 如果存在，那么去存放所有表数据的表，将所有属于该数据库且删除标记为FALSE的表的删除标记改为TRUE
    # 表示已经删除
    db_table_temp.loc[db_table_temp["db_name"] == db, 'is_del'] = True
    # 获得数据库id
    db_id_temp = db_table_temp.at[index, 'db_id']
    db_table_temp.to_csv(DB_META_DATA_PATH, index=False, sep=",")
    # 查找存放所有表数据的表，选择所有属于该数据库且删除标记为FALSE的元组（也就是属于该数据库的表）
    # 如果有元组被选择，将上述元组的删除标记改为TRUE，表示已经删除
    tables = pd.read_csv(TB_META_DATA_PATH)
    tables.loc[tables["db_id"] == db_id_temp, 'is_del'] = True
    tables.to_csv(TB_META_DATA_PATH, index=False, sep=",")

def droptable(instr,dbname):
        # 解析sql语句，如果符合删除数据库的正则表达式，那么从语句中得到要删除的表的名称
        _, _, tb = instr.split(" ")
        db_table_temp = pd.read_csv(DB_META_DATA_PATH)
        try:
            # 如果数据库表文件中有这个名称对应的并且其删除标记为FALSE的元组，继续
            index = \
                db_table_temp[
                    (db_table_temp["db_name"] == dbname) &\
                    (db_table_temp["is_del"] == False)].index.tolist()[0]
        except:
            # 提示选择数据库
            print("Error: 没有" + dbname + "数据库！")
            exit()
        # 获得数据库id
        db_id_temp = db_table_temp.at[index, 'db_id']
        tables = pd.read_csv(TB_META_DATA_PATH)
        try:
            # 查找存放所有表数据的表，选择所有属于该数据库且表名为需要删除的表名，删除标记为FALSE的元组
            temp = tables[(tables["table_name"] == tb) & (tables["db_id"] == db_id_temp) \
            & (tables["is_del"] == False)].index.tolist()[0]
        except:
            # 如果没有元组被选择，提示要删除的表不存在
            print("Error: 没有" + tb + "表！")
            exit()
        # 如果有元组被选择，将上述元组的删除标记改为TRUE，表示已经删除
        tables.loc[(tables["table_name"] == tb) & (tables["db_id"] == db_id_temp), "is_del"] = True
        tables.to_csv(TB_META_DATA_PATH, index=False, sep=",")

def deletedata(instr,dbname):
        _, _, tb, _, condition = instr.split(" ")
        db_table_temp = pd.read_csv(DB_META_DATA_PATH)
        try:
            # 从全局变量获得现在选择的数据库名称
            # 如果数据库表文件中有这个名称对应的并且其删除标记为FALSE的元组，继续
            index = \
                db_table_temp[
                    (db_table_temp["db_name"] == dbname) &\
                    (db_table_temp["is_del"] == False)].index.tolist()[0]
        except:
            # 否则，提示选择数据库
            print("Error: 没有" + dbname + "数据库！")
            exit()
        # 获得数据库id
        db_id_temp = db_table_temp.at[index, 'db_id']
        try:
            #按照相同方式寻找表
            tables = pd.read_csv(dbname + "\\" + tb + ".csv")
            tables1 = pd.read_csv(TB_META_DATA_PATH)
            temp = tables1[(tables1["table_name"] == tb) & (tables1["db_id"] == db_id_temp) & (
                    tables1["is_del"] == False)].index.tolist()[0]
            meta_data_df = pd.read_csv(TB_META_DATA_PATH)
            index_m = meta_data_df[meta_data_df["table_name"] == tb].index.tolist()[0]
        except:
            print("Error: 没有" + tb + "表！")
            exit()

        # 读取要删除的表项所在的表，然后删除所有满足筛选条件的行
        if condition.find("<") != -1:
            condition_list = condition.split("<")
            tables = tables.drop(tables[tables[condition_list[0]] < int(condition_list[1])].index)
        elif condition.find(">") != -1:
            condition_list = condition.split(">")
            tables = tables.drop(tables[tables[condition_list[0]] > int(condition_list[1])].index)
        elif condition.find("=") != -1:
            condition_list = condition.split("=")
            # 修改，索引和非索引
            dbpath = os.path.join(BASE_PATH, dbname)
            indextable_path = os.path.join(dbpath, tb + "_index.csv")
            temp_table_index = pd.read_csv(indextable_path)
            primkey = str(meta_data_df.loc[index_m, "primary_key"])
            if(condition_list[0] == primkey):
                idx1 = binsearch(temp_table_index ,condition_list[0],condition_list[1])
                tables = tables.drop(idx1)
            else:
                tables = tables.drop(tables[tables[condition_list[0]] == int(condition_list[1])].index)
            
        tables.to_csv(dbname + "\\" + tb + ".csv", index=False, sep=",")
        
# --------------------------------------------------------------------------------------------

# 分析语句
def analyse_instr(instr, dbname):
    # 拆出单词
    db_path = os.path.join(BASE_PATH, dbname)
    tokens = re.split(r"([ ,();=])", instr.lower().strip())
    tokens = [t for t in tokens if t not in [' ', '', '\n']]
    # print(tokens)
    # 创建数据库
    if tokens[0] == "create":
        if tokens[1] == "database": #数据库
            create_database(tokens)
        elif tokens[1] == "table": #表
            create_table(tokens,dbname,db_path)
        else:
            print("Invalid input!")

    # show
    elif tokens[0] == "show":
        if tokens[1] == "databases":
            show_database()
        elif tokens[1] == "tables":
            show_table(dbname)
        else:
            print("Invalid input!")

    # update
    elif re.fullmatch(update_instr, instr):
        update(instr,db_path)
    
    #select 
    elif tokens[0] == "select":
        if tokens[1] == "*":
            select_all(instr,db_path)
        elif re.fullmatch(select_table_instr, instr):
            select_table(instr,db_path)
        elif re.fullmatch(select_where_table_instr, instr):
            select_where_table(instr,db_path)
        

    # 插入数据，正则表达式匹配
    #insert
    elif re.fullmatch(insert_instr, instr):
        insert_data(instr,db_path)

    # drop database
    elif tokens[0]=="drop":
        if tokens[1]=="database":
            dropdatabase(instr)
        elif tokens[1]=="table":
            droptable(instr,dbname)
        else:
            print("Invalid input!")

    #delete
    elif re.fullmatch(delete_where_table_instr, instr):
        deletedata(instr,dbname)

    else:
        print("Invalid input!")




def main():
    init_meta_data()
    init_databases_table()
    instr = str(input("Please enter the instruction: \n"))
    db_name = DEFAULT_DB_NAME
    
    while instr != "exit":
        # use database
        if re.fullmatch(use_dbs_instr, instr):
            db_name = analyse_use_db(instr)
        else:
            analyse_instr(instr, db_name)
        instr = str(input("\ninput your instruction:\n"))
    print("Exit successfully!")


if __name__ == '__main__':
    main()
