#!/usr/bin/python3
from termcontrol import widget, widgetScreen, widgetBoxScreen

s=widgetScreen(fg=14, bg=233)
s.stream.feed(s.t.drawRuler(s.w, s.h))
box=s.addWidget(widgetBoxScreen(23, 5, 20, 10, theme='curve', bg=233, termBg=24))
box2=s.addWidget(widgetBoxScreen(53, 50, 20, 10, theme='curve', bg=233, termBg=236))
buffer=box.t.gotoxy(1,1)+"Testing 123"
box.stream.feed(buffer)
box2.stream.feed(box2.t.gotoxy(3,3)+'hello')
print(s.draw()+s.t.gotoxy(1,1))
input()
