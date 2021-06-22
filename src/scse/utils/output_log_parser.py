
# Parse the customer orders from the output log
def get_customer_orders():
    with open("../main/gym/output.log") as file:
        all_orders = []
        orders_in_time_step={}
        for line in file:
            if line.startswith('DEBUG:scse.controller.miniscot:clock') and orders_in_time_step:
                all_orders.append(orders_in_time_step)
                orders_in_time_step={}
            if line.startswith('DEBUG:scse.modules.customer.mqcnn_rfs_customer_order'):
                parse_ints=[int(s) for s in line.split() if s.isdigit()]
                orders_in_time_step["{:01d}".format(parse_ints[0])]=parse_ints[1]
        # append last:
        if orders_in_time_step:
            all_orders.append(orders_in_time_step)

        # for i in range(len(all_orders)):
        #     print(all_orders[i])
        print(all_orders)

if __name__ == '__main__':
    get_customer_orders()