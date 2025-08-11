from task_manager import Task_manager
tm = Task_manager()

tasks = tm.read_df_from_csv()
target_task = tasks.loc[tasks["is_target"] == 1]
for i,r in target_task.iterrows():
    print(i,r)
    
