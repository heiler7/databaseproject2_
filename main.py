import pandas as pd
import os
import time
import re

BASE_PATH = os.getcwd()
DB_META_DATA_PATH = os.path.join(BASE_PATH, r"meta_data\database_meta_data.csv")
TB_META_DATA_PATH = os.path.join(BASE_PATH, r"meta_data\table_meta_data.csv")
DEFAULT_DB_NAME = "xsj"

# 显示所有列
pd.set_option('display.max_columns', None)
# 显示所有行
pd.set_option('display.max_rows', None)

# 选择数据库
use_dbs_instr = r"use\b\s[a-zA-Z0-9_]+"
#insert语句
insert_instr="insert\\b\\sinto\\b\\s[a-zA-Z0-9_]+\\b\\svalues\((([0-9]*)|([a-zA-Z0-9_]*))?(\,([0-9]*)|([a-zA-Z0-9_]*))*\)"
#update语句
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


# 初始化元数据库表
def init_databases_table():
    try:
        db_meta_data_pd = pd.read_csv(DB_META_DATA_PATH)
    except FileNotFoundError:
        db_meta_data_columns = ["db_id", "db_name", "create_time", "is_del"]
        db_meta_data_pd = pd.DataFrame(columns=db_meta_data_columns, index=[0])
        db_meta_data_pd.to_csv(DB_META_DATA_PATH, index=False, sep=",")


# 初始化元数据表
def init_meta_data():
    try:
        tb_meta_data_pd = pd.read_csv(TB_META_DATA_PATH)
    except FileNotFoundError:
        tb_meta_data_columns = ["db_id", "table_id", "table_name", "column_list",
                                "type_list", "primary_key","foreign_key",
                                "row_num", "size_in_byte", "modify_time", 
                                "create_time", "uid", "gid", "is_del"]
        tb_meta_data_pd = pd.DataFrame(columns=tb_meta_data_columns, index=[0])
        tb_meta_data_pd.to_csv(TB_META_DATA_PATH, index=False, sep=",")


def analyse_use_db(instr):
    _, db_name = instr.split(" ")
    db_meta_data_df = pd.read_csv(DB_META_DATA_PATH)
    is_del = db_meta_data_df[db_meta_data_df["db_name"] == db_name]["is_del"].values.tolist()[0]
    if db_name not in db_meta_data_df["db_name"].values or is_del == True:
        print("Error: database`", db_name, "`not exist! ")
        exit()
    print("current database:", db_name)
    return db_name


# 分析语句
def analyse_instr(instr, use_db_name):
    # 拆出单词
    USE_DATABASE_PATH = os.path.join(BASE_PATH, use_db_name)
    tokens = re.split(r"([ ,();=])", instr.lower().strip())
    tokens = [t for t in tokens if t not in [' ', '', '\n']]

    if tokens[0] == "create" and tokens[1] == "database":
        db_meta_data_df = pd.read_csv(DB_META_DATA_PATH)
        if pd.isnull(db_meta_data_df.loc[0, "db_id"]):
            db_id = 0
        else:
            db_id = db_meta_data_df.shape[0]
        new_db_name = tokens[2]
        if not os.path.exists(new_db_name):
            os.mkdir(new_db_name)
            print("create database", new_db_name, "successfully!")
        else:
            print("Error: database already exist! ")
            exit()
        db_stat = os.stat(new_db_name)
        db_meta_data_df.loc[db_id, "db_id"] = db_id
        db_meta_data_df.loc[db_id, "db_name"] = new_db_name
        db_meta_data_df.loc[db_id, "create_time"] = time.ctime(db_stat.st_ctime)
        db_meta_data_df.loc[db_id, "is_del"] = False
        db_meta_data_df.to_csv(DB_META_DATA_PATH, index=False, sep=",")

    elif tokens[0] == "show" and tokens[1] == "databases":
        db_meta_data_df = pd.read_csv(DB_META_DATA_PATH)
        db_name_list = db_meta_data_df[db_meta_data_df["is_del"] == False]["db_name"].values
        for db_name in db_name_list:
            print(db_name)

    elif tokens[0] == "create" and tokens[1] == "table":
        # 读取元库数据并获得所属数据库id
        db_meta_data_df = pd.read_csv(DB_META_DATA_PATH)
        db_id = int(db_meta_data_df[db_meta_data_df["db_name"] == use_db_name]["db_id"].values[0])
        # 读取元表数据并为新表分配id
        tb_meta_data_df = pd.read_csv(TB_META_DATA_PATH)
        if pd.isnull(tb_meta_data_df.loc[0, "table_id"]):
            table_id = 0
        else:
            table_id = tb_meta_data_df.shape[0]
        # 获取新表name
        new_tb_name = tokens[2]
        temp_df = tb_meta_data_df[tb_meta_data_df["is_del"] == False]
        tb_name_list = temp_df[temp_df["db_id"] == db_id]["table_name"].values
        if new_tb_name in tb_name_list:
            print("Error: table", new_tb_name, "already exist! ")
            exit()
        # 获取新表属性以及类型
        col_tokens = [] # 属性和类型list
        if "primary" in tokens:
            col_tokens = tokens[4:tokens.index("primary")-1]
        else:
            col_tokens = tokens[4:-1]
        # 属性list
        col_name_list = col_tokens[::3]
        # 类型list
        col_type_list = col_tokens[1::3]
        # 判断属性和类型数目是否相同
        if len(col_name_list) != len(col_type_list):
            print("Error: type error.")
            exit()
        # 判断类型必须是已有的类型
        for i in col_type_list:
            if i not in type_list:
                print("Error: type error.")
                exit()
        # 设置主键
        pk = ""
        if "primary" in tokens:
            pk = tokens[tokens.index("primary")+3]
            if pk not in col_name_list:
                print("Error: primary key error.")
                exit()
        # 设置外键
        fk = "null"
        fk_r = ""
        if "foreign" in tokens:
            fk = tokens[tokens.index("foreign")+3]              # 设置的外键值
            if "references" in tokens:
                fk_r = tokens[tokens.index("references")+1]     # 外键所在的表
                fk_r_v = tokens[tokens.index("references")+3]   # 外键值
                # 设置的外键矛盾，报错
                if fk != fk_r_v:
                    print("Error: foreign key error.")
                    exit()
            # 没有references，报错
            else:
                print("Error: foreign key error.")
                exit()
            temp_df = tb_meta_data_df[tb_meta_data_df["is_del"] == False]
            fk_r_cols = temp_df[temp_df["table_name"] == fk_r].values
            print(fk_r_cols)
            # 没有references的表，报错
            if fk_r_v not in fk_r_cols:
                print("Error: foreign key error.")
                exit()
            else:
                fk_type = temp_df[temp_df["table_name"] == fk_r]["type_list"].values.tolist()[0]
                col_name_list.append(fk)
                print(fk_type)
                col_type_list.append(fk_type)
        # 新增表
        new_table_df = pd.DataFrame(columns=col_name_list)
        new_table_path = os.path.join(USE_DATABASE_PATH, new_tb_name + ".csv")
        new_table_df.to_csv(new_table_path, index=False, sep=',')
        print("create table", new_tb_name, "successfully!")
        table_stat = os.stat(new_table_path)
        # 更新表元数据
        join_str = ' '
        col_name_str = join_str.join(col_name_list)
        col_type_str = join_str.join(col_type_list)
        tb_meta_data_df.loc[table_id, 'db_id'] = db_id
        tb_meta_data_df.loc[table_id, 'table_id'] = table_id
        tb_meta_data_df.loc[table_id, 'table_name'] = new_tb_name
        tb_meta_data_df.loc[table_id, 'column_list'] = col_name_str
        tb_meta_data_df.loc[table_id, 'type_list'] = col_type_str
        tb_meta_data_df.loc[table_id, 'primary_key'] = pk
        tb_meta_data_df.loc[table_id, 'foreign_key'] = fk
        tb_meta_data_df.loc[table_id, 'row_num'] = 0
        tb_meta_data_df.loc[table_id, 'size_in_byte'] = table_stat.st_size
        tb_meta_data_df.loc[table_id, 'modify_time'] = time.ctime(table_stat.st_mtime)
        tb_meta_data_df.loc[table_id, 'create_time'] = time.ctime(table_stat.st_ctime)
        tb_meta_data_df.loc[table_id, 'uid'] = table_stat.st_uid
        tb_meta_data_df.loc[table_id, 'gid'] = table_stat.st_gid
        tb_meta_data_df.loc[table_id, 'is_del'] = False
        tb_meta_data_df.to_csv(TB_META_DATA_PATH, index=False, sep=',')

    elif re.fullmatch(insert_instr, instr):
        # INSERT INTO table_name values(a,b,c,d) 命令格式
        tokens=[i for i in re.split(r"([ ,();=])", instr.lower().strip()) if i not in[' ',',',')','(','']]
        table_name=tokens[2]
        idx=tokens.index("values")

        table_path = os.path.join(USE_DATABASE_PATH, table_name + ".csv")
        try:
            table_df = pd.read_csv(table_path)
            meta_data_df = pd.read_csv(TB_META_DATA_PATH)
            index = meta_data_df[meta_data_df["table_name"] == table_name].index.tolist()[0]
        except FileNotFoundError:
            print("Error: file not found.")
            exit()
        table_num = table_df.shape[1]
        new = {}
        insert_num=len(tokens)-idx-1
        if insert_num>table_num:#插入值过多
            print("Error: too many values.")
            exit()
            
        
        for column in table_df.columns:
            # print("input {}:".format(column))
            idx+=1
            new[column] = tokens[idx]
        table_df.loc[table_num] = list(new.values())

        # 外键约束
        fk = str(meta_data_df.loc[index, "foreign_key"])
        if fk == "null":
            pass
        elif fk.count(" ") == 1:
            rtable, fk_v = fk.split(" ")
            try:
                rtable_path = os.path.join(USE_DATABASE_PATH, rtable + ".csv")
                rdf = pd.read_csv(rtable_path)
            except FileNotFoundError:
                print("Error: file not found.")
                exit()
            if new[fk_v] not in [str(i) for i in list(rdf.loc[:, fk_v])]:
                print("Error: fk constraint error.")
                exit()

        # 主键约束
        pk = str(meta_data_df.loc[index, "primary_key"])
        if new[pk] in [str(i) for i in list(table_df.loc[:, pk][: -1])]:
            print("Error: pk constraint error.")
            exit()

        table_df.to_csv(table_path, index=False, sep=',')
        stat = os.stat(table_path)

        meta_data_df.loc[index, "row_num"] += 1
        meta_data_df.loc[index, "modify_time"] = time.ctime(stat.st_mtime)
        meta_data_df.loc[index, "size_in_byte"] = stat.st_size
        meta_data_df.to_csv(TB_META_DATA_PATH, index=False, sep=',')
        print("insert successfully!")

    elif tokens[0] == "show" and tokens[1] == "tables":
        db_meta_data_df = pd.read_csv(DB_META_DATA_PATH)
        db_id = int(db_meta_data_df[db_meta_data_df["db_name"] == use_db_name]["db_id"].values[0])
        tb_meta_data_df = pd.read_csv(TB_META_DATA_PATH)
        temp_df = tb_meta_data_df[tb_meta_data_df["is_del"] == False]
        tb_name_list = temp_df[temp_df["db_id"] == db_id]["table_name"].values
        for tb_name in tb_name_list:
            print(tb_name)

    elif tokens[0] == "show" and tokens[1] == "meta" and tokens[2] == "data":
        tb_meta_data_df = pd.read_csv(TB_META_DATA_PATH)
        db_meta_data_df = pd.read_csv(DB_META_DATA_PATH)
        print('table_meta_data:', tb_meta_data_df.columns.values)
        print('database_meta_data:', db_meta_data_df.columns.values)

    elif re.fullmatch(update_instr, instr):
        # update Person set FirstName=a where LastName=b 
        tokens=[i for i in re.split(r"([ ,();=])", instr.lower().strip()) if i not in[' ',',',')','(','','=']]
        table_name=tokens[1]

        table_path = os.path.join(USE_DATABASE_PATH, table_name + ".csv")
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
            if(len(table_df.loc[table_df[attr]==attrv,change_item].index)==0):
                exit()
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

    elif tokens[0] == "select" and tokens[1] == "*":
        table_name = tokens[3]
        try:
            table_path = os.path.join(USE_DATABASE_PATH, table_name + ".csv")
            table_df = pd.read_csv(table_path)
        except FileNotFoundError:
            print("Error: file not found.")
            exit()
        print(table_df)

    elif re.fullmatch(select_table_instr, instr):
        _, attr, _, table_name = instr.split(" ")
        attr_list = attr.split(",")
        try:
            table_path = os.path.join(USE_DATABASE_PATH, table_name + ".csv")
            table_df = pd.read_csv(table_path)  # zxc  修改："tables\\" -> db_name+"\\"
        except FileNotFoundError:
            print("Error: file not found.")
            exit()
        print(table_df.loc[:, attr_list])

    elif re.fullmatch(select_where_table_instr, instr):
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
            table_df = pd.read_csv(os.path.join(USE_DATABASE_PATH, table_name + ".csv"))  # zxc  修改："tables\\" -> db_name+"\\"
        except FileNotFoundError:
            print("Error: file not found.")
            exit()
        t2 = int(round(time.time() * 1000))
        if condition_list[-1] == "=":
            ans = table_df[table_df[condition_list[0]] == int(condition_list[1])]
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
    # 删除数据库
    elif re.fullmatch(drop_database_instr, instr):
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
    # 删除表
    elif re.fullmatch(drop_table_instr, instr):
        # 解析sql语句，如果符合删除数据库的正则表达式，那么从语句中得到要删除的表的名称
        _, _, tb = instr.split(" ")
        db_table_temp = pd.read_csv(DB_META_DATA_PATH)
        try:
            # 如果数据库表文件中有这个名称对应的并且其删除标记为FALSE的元组，继续
            index = \
                db_table_temp[
                    (db_table_temp["db_name"] == use_db_name) &\
                    (db_table_temp["is_del"] == False)].index.tolist()[0]
        except:
            # 提示选择数据库
            print("Error: 没有" + use_db_name + "数据库！")
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
    # 删除表项
    elif re.fullmatch(delete_where_table_instr, instr):
        # 解析sql语句，如果符合删除数据库的正则表达式
        # 那么从语句中得到要删除的表项所在的表的名称以及筛选条件
        _, _, tb, _, condition = instr.split(" ")
        db_table_temp = pd.read_csv(DB_META_DATA_PATH)
        try:
            # 从全局变量获得现在选择的数据库名称
            # 如果数据库表文件中有这个名称对应的并且其删除标记为FALSE的元组，继续
            index = \
                db_table_temp[
                    (db_table_temp["db_name"] == use_db_name) &\
                    (db_table_temp["is_del"] == False)].index.tolist()[0]
        except:
            # 否则，提示选择数据库
            print("Error: 没有" + use_db_name + "数据库！")
            exit()
        # 获得数据库id
        db_id_temp = db_table_temp.at[index, 'db_id']
        try:
            # 查找存放所有表数据的表，选择所有属于该数据库且表名为需要删除的表名，删除标记为FALSE的元组
            # 如果有元组被选择，说明要删除的表项所在的表存在，继续
            tables = pd.read_csv(use_db_name + "\\" + tb + ".csv")
            tables1 = pd.read_csv(TB_META_DATA_PATH)
            temp = tables1[(tables1["table_name"] == tb) & (tables1["db_id"] == db_id_temp) & (
                    tables1["is_del"] == False)].index.tolist()[0]
        except:
            # 如果没有元组被选择，提示要删除的表项所在的表不存在
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
            tables = tables.drop(tables[tables[condition_list[0]] == int(condition_list[1])].index)
        tables.to_csv(use_db_name + "\\" + tb + ".csv", index=False, sep=",")
    # 语法错误
    else:
        print("Error: You have an error in your SQL syntax.")
        exit()


def main():
    init_meta_data()
    init_databases_table()
    instr = str(input("input your instruction:\n"))
    db_name = DEFAULT_DB_NAME
    while instr != "quit":
        # use database
        if re.fullmatch(use_dbs_instr, instr):
            db_name = analyse_use_db(instr)
        else:
            analyse_instr(instr, db_name)
        instr = str(input("\ninput your instruction:\n"))
    print("quit successfully!")


if __name__ == '__main__':
    main()

"""
测试用例：
【已经修改】
0. 选择数据库 默认是xsj
use wyj
1. 创建数据库
create database wyj

2. 创建表course：
create table course(cid int, cname varchar, ctime int, primary key(cid))

3. 创建表student：
create table student(sid int, sname varchar, age int, primary key(sid) foreign key(cid) references course(cid))

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
