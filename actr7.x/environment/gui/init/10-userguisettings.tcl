# this file generated when environment is closed
# refresh . to make sure sizes are right

wm deiconify .
update
wm withdraw .
if {[winfo screenwidth .] != 1920 || [winfo screenheight .] != 1080 || [lindex [wm maxsize .] 0] != 5764 || [lindex [wm maxsize .] 1] != 1421} {
  set size_mismatch 1
} else {
  set size_mismatch 0
}

if $size_mismatch {
  set reset_window_sizes [tk_messageBox -icon warning -title "Screen resolution changed" -type yesno \
                                         -message "The screen resolution is not the same as it was the last time the Environment was used.  Should the window positions reset to the defaults?"]
} else { set reset_window_sizes 0}
if {$reset_window_sizes != "yes"} {
  set window_config(.whynotdm) 469x300+342+402
  set changed_window_list(.whynotdm) 1
  set window_config(.visicon) 1920x1009+116+84
  set changed_window_list(.visicon) 1
  set window_config(.stepper) 773x544+-2750+188
  set changed_window_list(.stepper) 1
  set window_config(.declarative) 793x300+346+445
  set changed_window_list(.declarative) 1
  set window_config(.control_panel) 235x685+385+231
  set changed_window_list(.control_panel) 1
  set window_config(.visicon_history) 810x340+555+370
  set changed_window_list(.visicon_history) 1
  set window_config(.whynot) 605x300+-3026+500
  set changed_window_list(.whynot) 1
  set window_config(.buffers) 577x240+957+309
  set changed_window_list(.buffers) 1
  set window_config(.procedural) 919x360+-3732+225
  set changed_window_list(.procedural) 1
  set window_config(.copyright) 400x190+760+395
  set changed_window_list(.copyright) 1
}
set gui_options(p_selected) #44DA22
set gui_options(p_matched) #FCA31D
set gui_options(p_mismatched) #E1031E
