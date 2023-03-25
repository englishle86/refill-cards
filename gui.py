import datetime
import pickle
from tkinter import *
from tkinter import simpledialog
from tkinter import ttk

from connection import ShopifyConnector
from pdf import RefillCardGenerator

DEBUG = False


class RefillCardsGui:
    def gen_pdf(self, products, name):
        products = map(lambda p: (p[0][:55], p[1], p[2]), products)
        generator = RefillCardGenerator()
        return generator.generate_pdf(products, name)

    def refresh(self):
        self.orders_dict = self.connector.get_orders_list()
        values = list(self.orders_dict.keys())
        values.sort()
        self.order_entry.configure(values=values)

        values.sort(key=len)
        if len(values) == 0:
            max_len = 0
        else:
            max_len = len(values[-1]) - 5
        self.order_entry.configure(width=max_len)

    def print_all(self):
        products = self.connector.get_all_products()
        pdf_created = self.gen_pdf(products, "all.pdf")
        if pdf_created:
            self.filename_label.configure(text="File saved to: all.pdf")

    def order_selected(self, event):
        order_id = self.orders_dict[self.order_entry.get()]
        if DEBUG:
            products = pickle.load(open("last_order_selected.pickle", "rb"))
        else:
            products = self.connector.get_cards_needed_list(order_id)
            pickle.dump(products, open("last_order_selected.pickle", "wb"))
        filename = "{}.pdf".format(self.order_entry.get())
        pdf_created = self.gen_pdf(products, filename)
        if pdf_created:
            self.filename_label.configure(text="File saved to: {}".format(filename))
        else:
            self.filename_label.configure(text="Error generating PDF")

    def __init__(self):
        self.root = Tk()
        self.root.title("Refill Cards")

        # self.start_date = StringVar()
        # year = datetime.date.today().year
        # if datetime.date.today().month < 11:
        #    year -= 1
        # self.start_date.set("{}-11-01".format(year))

        # self.connector = ShopifyConnector(self.start_date.get())

        # self.master.wait_window(self.w.top)

        # self.connector = ShopifyConnector("2020-03-01")

        self.mainframe = ttk.Frame(self.root, padding="3 3 12 12")
        self.mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
        self.mainframe.columnconfigure(0, weight=1)
        self.mainframe.rowconfigure(0, weight=1)

        wait_label = ttk.Label(self.mainframe, text="Waiting for start/end dates...")
        wait_label.grid(column=0, row=0, sticky=W)

        default_date = str(datetime.date.today() - datetime.timedelta(weeks=2))
        default_date_end = str(datetime.date.today())
        date_selection_start = simpledialog.askstring(title="Orders start date",
                                                      prompt="First, enter orders start date (YYYY-MM-DD)",
                                                      initialvalue=default_date)
        if date_selection_start == None:
            exit()
        date_selection_end = simpledialog.askstring(title="Orders end date",
                                                    prompt="Second, enter orders end date (YYYY-MM-DD)",
                                                    initialvalue=default_date_end)
        if date_selection_end == None:
            exit()

        wait_label['text'] = "Loading..."
        self.root.update()
        debug_orders = pickle.load(open("last_results.pickle", "rb")) if DEBUG else []

        self.connector = ShopifyConnector(date_selection_start.strip(), date_selection_end.strip(), debug_orders)
        self.orders_dict = ()

        wait_label['text'] = ""

        # ttk.Label(self.mainframe, text="Season Start Date: ").grid(column=0, row=0, sticky=W)
        # self.start_date_entry = ttk.Entry(self.mainframe, width=10, textvariable=self.start_date)
        # self.start_date_entry.grid(column=1, row=0, sticky=(W, E))

        ttk.Label(self.mainframe, text="Cards: ").grid(column=0, row=2, sticky=W)
        self.filename_label = ttk.Label(self.mainframe, text="--")
        self.filename_label.grid(column=1, row=2, sticky=(W, E))

        self.order = StringVar()
        ttk.Label(self.mainframe, text="Order: ").grid(column=0, row=1, sticky=W)
        self.order_entry = ttk.Combobox(self.mainframe, width=7, textvariable=self.order, values=(1, 2, 3),
                                        state="readonly")
        self.order_entry.bind("<<ComboboxSelected>>", self.order_selected)
        self.order_entry.grid(column=1, row=1, sticky=(W, E))
        ttk.Button(self.mainframe, text="Refresh", command=self.refresh).grid(column=2, row=1, sticky=W)
        ttk.Button(self.mainframe, text="Print All", command=self.print_all).grid(column=2, row=2, sticky=W)

        for child in self.mainframe.winfo_children(): child.grid_configure(padx=5, pady=5)

    def run(self):
        self.refresh()
        self.order_entry.focus()
        self.root.mainloop()


if __name__ == '__main__':
    gui = RefillCardsGui()
    gui.run()
