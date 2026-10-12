# Pin the reference design's CoreVectorBlox component in a WORK_DIR copy.
# The case-study handoff confirms 2.0.1 / PRESET:0 as V250, with 128-bit M_AXI.
# Source: deps/tychon-quantum-sensing/workers/polarfire-hybrid-control/docs/rung_f_v250_post_program_handoff_2026-06-16.md:21-33
# V500 and V1000 preset mappings remain unconfirmed.
if {$argc != 3} {
    puts stderr "usage: tclsh pin_vectorblox.tcl component.tcl CORE_VERSION VBX_SIZE"
    exit 2
}
lassign $argv component version size
if {![regexp {^[0-9]+\.[0-9]+\.[0-9]+$} $version]} {error "invalid CORE_VERSION"}
array set preset {V250 0 V500 1 V1000 2}
if {![info exists preset($size)]} {error "VBX_SIZE must be V250, V500, or V1000"}
set fd [open $component r]
set content [read $fd]
close $fd
set resize [file join [file dirname $component] vectorblox_axi_resize.tcl]
set fd [open $resize r]
set resize_content [read $fd]
close $fd
set source_vlnv {Microchip:SolutionCore:core_vectorblox:*}
set source_preset {"PRESET:1"}
if {[string first $source_vlnv $content] < 0 ||
    [string first $source_vlnv $content [expr {[string first $source_vlnv $content] + 1}]] >= 0 ||
    [string first $source_preset $content] < 0 ||
    [string first $source_preset $content [expr {[string first $source_preset $content] + 1}]] >= 0 ||
    [string first {"M_AXI_DATA_WIDTH:128"} $content] < 0} {
    error "reference component differs from pinned v2026.04 input"
}
set source_id_width {"ID_WIDTH:3"}
if {[string first $source_id_width $resize_content] < 0 ||
    [string first $source_id_width $resize_content [expr {[string first $source_id_width $resize_content] + 1}]] >= 0} {
    error "vectorblox_axi_resize.tcl lacks exactly one ID_WIDTH:3 parameter"
}
set content [string map [list $source_vlnv "Microchip:SolutionCore:core_vectorblox:$version" \
                           $source_preset "\"PRESET:$preset($size)\""] $content]
set resize_content [string map [list $source_id_width {"ID_WIDTH:4"}] $resize_content]
set fd [open $component w]
puts -nonewline $fd $content
close $fd
set fd [open $resize w]
puts -nonewline $fd $resize_content
close $fd
set size_note "$size mapping unconfirmed"
if {$size eq "V250" && $version eq "2.0.1"} {set size_note "V250 confirmed by case study"}
puts "Pinned core_vectorblox to $version with PRESET:$preset($size) ($size_note); vectorblox_axi_resize ID_WIDTH:4"
