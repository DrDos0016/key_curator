# coding=utf-8
from __future__ import unicode_literals
from Tkinter import *
from glob import glob
from PIL import Image, ImageTk
from sys import exit
import tkFileDialog, tkSimpleDialog
import os, shutil

class GUI(object):
    def __init__(self, size="800x600", root=""):
        self.idx = 0
        self.size = size
        self.root = root
        self.files = []
        self.file_count = 0
        self.widgets = {}
        
        self.fit_image = True
        self.resize_method = Image.NEAREST # Image.ANTIALIAS / NEAREST
        
        self.category_tree = []
        self.categories = {}
        self.destinations = []
        self.destinations_text = ""

    def apply(self, *args):
        if len(self.destinations) >= 2:
            for dest in self.destinations:
                output_path = os.path.join(self.root, dest, os.path.basename(self.files[self.idx]))
                shutil.copy2(self.files[self.idx], output_path)
            
            self.delete()  
        elif len(self.destinations) == 1:
            output_path = os.path.join(self.root, self.destinations[0], os.path.basename(self.files[self.idx]))
            shutil.move(self.files[self.idx], output_path)
            
            to_delete = self.files.pop(self.idx)
            self.file_count = len(self.files)
            if self.idx >= self.file_count:
                self.idx = 0
            self.draw_pic()
            
        self.destinations = []
        self.destinations_text = ""
        self.widgets["destinations"].config(text=self.destinations_text.title())
        return True

    def bind_keys(self):
        # Bind keys
        self.window.bind("<Escape>", quit)
        self.window.bind("<Left>", self.prev)
        self.window.bind("<Right>", self.next)
        self.window.bind("<Delete>", self.delete) # Delete file
        self.window.bind_all("<Up>", self.prev_category)
        self.window.bind_all("<Key>", self.categorize)
        self.window.bind("<BackSpace>", self.top_category) # Top Category
        self.window.bind("<`>", self.draw_pic) # Refresh
        self.window.bind("<space>", self.view) # View Image
        self.window.bind("<Return>", self.apply) # Apply
        self.window.bind("<Configure>", self.resize) # Resized window
        return True

    def categorize(self, key, *args):
        key = key.keysym
        if key not in "abcdefghijklmnopqrstuvwxyz1234567890" or not self.categories.get(key):
            return False
        
        destination = self.categories[key]
        if destination[-4:] == ".cfg":
            self.load_categories(destination)
            return True
        
        if destination not in self.destinations:
            self.destinations.append(destination)
            if self.destinations_text != "":
                self.destinations_text += ", "
            self.destinations_text += destination.split(os.sep)[-1]
        else: # Remove from list
            new_dests = []
            for dest in self.destinations:
                if dest != destination:
                    new_dests.append(dest)
            self.destinations = new_dests
            self.destinations_text = ", ".join(self.destinations)
            
        self.widgets["destinations"].config(text=self.destinations_text.title())
        return True

    def create_widgets(self, title):
        self.window = Tk()
        self.window.title(title)
        self.window.geometry(self.size)
        self.window.update()
        
        # Create widgets
        self.widgets["menubar"] = Menu(self.window)
        self.widgets["menubar"].add_command(label="Open Directory", command=self.open)
        #self.widgets["menubar"].add_command(label="Rename Image", command=self.rename)
        self.widgets["menubar"].add_command(label="View Image", command=self.view)
        self.widgets["menubar"].add_command(label="Refresh", command=self.draw_pic)
        self.widgets["menubar"].add_command(label="Toggle Full/Fit", command=self.toggle_fit)
        self.widgets["menubar"].add_command(label="Toggle Fast/Best Resize", command=self.toggle_resize_method)
        self.window.config(menu=self.widgets["menubar"])
        
        self.widgets["resolution"] = Label(self.window, justify=LEFT)
        self.widgets["name"] = Label(self.window, justify=CENTER, text="X")
        self.widgets["name"].update()
        self.widgets["size"] = Label(self.window, justify=RIGHT)
        
        self.widgets["picture_frame"] = Frame(self.window, width=self.window.winfo_width(), height=self.window.winfo_height()-48)
        self.widgets["picture_frame"].update()
        self.widgets["picture"] = Label(self.widgets["picture_frame"], justify=CENTER)
        
        self.widgets["count"] = Label(self.window, justify=LEFT)
        self.widgets["destinations"] = Label(self.window, justify=CENTER)
        self.widgets["category"] = Label(self.window, justify=RIGHT)
        return True

    def delete(self, *args):
        to_delete = self.files.pop(self.idx)
        # Delete the file
        os.remove(to_delete)
        
        self.file_count = len(self.files)
        if self.idx >= self.file_count:
            self.idx = 0
        self.draw_pic()
        return True
       
    def draw_pic(self, *args):
        self.load_image()
        
        self.widgets["resolution"].config(text=str(self.image_w) + "x" + str(self.image_h))
        self.widgets["resolution"].grid(column=0,row=1, sticky=W, padx=5)
        
        self.widgets["name"].config(text=os.path.basename(self.filename))
        self.widgets["name"].grid(column=1,row=1, padx=5)
        
        self.widgets["size"].config(text=str(round(os.path.getsize(self.files[self.idx])/1024.0, 2)) +" KB")
        self.widgets["size"].grid(column=2,row=1, sticky=E, padx=5)
        
        self.widgets["picture_frame"].grid(column=0,row=2, sticky=(N,W,E,S), columnspan=3)
        self.widgets["picture"].config(image=self.image)
        
        # TODO: Fix first image not drawing correctly due to the picture frame being 1x1
        if self.widgets["picture_frame"].winfo_width() <= 1 or self.widgets["picture_frame"].winfo_height() <= 1:
            self.widgets["picture"].place(x=(self.window.winfo_width() - self.sized_w) / 2, y=(self.window.winfo_height() - self.sized_h) / 2 )
        else:
            self.widgets["picture"].place(x=(self.widgets["picture_frame"].winfo_width() - self.sized_w) / 2, y=(self.widgets["picture_frame"].winfo_height() - self.sized_h) / 2 )
        
        
        self.widgets["count"].config(text=str(self.idx+1)+"/"+str(len(self.files)))
        self.widgets["count"].grid(column=0,row=3, sticky=W, padx=5)
        
        self.widgets["destinations"].config(text=self.destinations_text)
        self.widgets["destinations"].grid(column=1,row=3, padx=5)
        
        self.widgets["category"].config(text=self.category_tree[-1].replace(".cfg", "").title())
        self.widgets["category"].grid(column=2,row=3, sticky=E, padx=5)
        return True
    
    def load_categories(self, file="default.cfg", no_add=False, *args):
        self.categories = {}
        fname = os.path.join("categories", file)
        file = open(fname)
        file = file.readlines()
        for line in file:
            if line[0] == "#":
                continue
            line = line.replace("\n","")
            line = line.replace("\r","")
            
            line = line.split("=", 2)
            key = line[0].lower()
            destination = line[1]
            self.categories[key] = destination
        if not no_add:
            self.category_tree.append(os.path.basename(fname))
        self.widgets["category"].config(text=self.category_tree[-1].replace(".cfg", "").title())
        return True
    
    def load_files(self):
        files = glob(os.path.join(self.root, "*.png"))
        files += glob(os.path.join(self.root, "*.jpg"))
        files += glob(os.path.join(self.root, "*.gif"))
        files += glob(os.path.join(self.root, "*.bmp"))
        files.sort()
        self.files = files
        self.idx = 0
        self.file_count = len(self.files)
        return True
    
    def load_image(self):
        filepath = self.files[self.idx]
        self.filename = os.path.basename(filepath)
        image = Image.open(filepath)
        (self.image_w, self.image_h) = image.size
        
        # Resize if needed
        if self.fit_image:
            if self.widgets["picture_frame"].winfo_width() <= 1 or self.widgets["picture_frame"].winfo_height() <= 1:
                image.thumbnail((self.window.winfo_width(), self.window.winfo_height()), self.resize_method)
            else:
                image.thumbnail((self.widgets["picture_frame"].winfo_width(), self.widgets["picture_frame"].winfo_height()), self.resize_method)
        
        (self.sized_w, self.sized_h) = image.size
        self.image = ImageTk.PhotoImage(image)
        return True
    
    def next(self, *args):
        if self.idx + 1 >= self.file_count:
            self.idx = 0
        else:
            self.idx += 1
        self.destinations = []
        self.destinations_text = ""
        self.draw_pic()
        return True
    
    def open(self):
        # Get image directory
        initial_dir = tkFileDialog.askdirectory(initialdir=self.root)
        print "DIR:", initial_dir
        if not initial_dir:
            return False
        self.root = initial_dir
        self.load_files()
        self.draw_pic()
        return True
        
    def prev(self, *args):
        if self.idx - 1 < 0:
            self.idx = self.file_count - 1
        else:
            self.idx -= 1
        self.destinations = []
        self.destinations_text = ""
        self.draw_pic()
        return True
        
    def prev_category(self, *args):
        if len(self.category_tree) > 1:
            self.category_tree = self.category_tree[:-1]
            self.load_categories(self.category_tree[-1], no_add=True)
        return True
        
    def rename(self, *args):
        return True
    
    def resize(self, *args):
        self.widgets["picture_frame"].config(width=self.window.winfo_width(), height=self.window.winfo_height()-48)
        return True
    
    def toggle_fit(self):
        self.fit_image = not self.fit_image
        self.draw_pic()
        return True
        
    def toggle_resize_method(self):
        if self.resize_method == Image.NEAREST:
            self.resize_method = Image.ANTIALIAS
        else:
            self.resize_method = Image.NEAREST
        self.draw_pic()
        return True
        
    def top_category(self, *args):
        self.category_tree = []
        self.categories = {}
        self.load_categories()
        return True
    
    def view(self, *args):
        to_open = self.files[self.idx]
        os.system(to_open)
        return True
    
def quit(*args):
    sys.exit()
    return True

def main():
    Gui = GUI()
    Gui.create_widgets("Key Curator")
    if os.name == "nt":
        initial = os.path.expanduser("~\\Pictures")
    else:
        initial = "~/pictures"
    #initial = "P:\\var\\projects\\misc\\key_curator\\pictures"
    initial_dir = tkFileDialog.askdirectory(initialdir=initial)
    if not initial_dir:
        exit()
    Gui.root = initial_dir.replace("/", os.sep)
    Gui.load_categories()
    Gui.load_files()
    Gui.bind_keys()
    Gui.draw_pic()
    Gui.window.mainloop()
    return True

if __name__ == "__main__": main()