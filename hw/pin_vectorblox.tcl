# Pin the reference design's CoreVectorBlox component in a WORK_DIR copy.
# PRESET is the exact parameter in the v2026.04 component export.
# Its numeric size mapping needs confirmation in the installed IP catalog.
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
set source_vlnv {Microchip:SolutionCore:core_vectorblox:*}
set source_preset {"PRESET:1"}
if {[string first $source_vlnv $content] < 0 ||
    [string first $source_vlnv $content [expr {[string first $source_vlnv $content] + 1}]] >= 0 ||
    [string first $source_preset $content] < 0 ||
    [string first $source_preset $content [expr {[string first $source_preset $content] + 1}]] >= 0 ||
    [string first {"M_AXI_DATA_WIDTH:128"} $content] < 0} {
    error "reference component differs from pinned v2026.04 input"
}
set content [string map [list $source_vlnv "Microchip:SolutionCore:core_vectorblox:$version" \
                           $source_preset "\"PRESET:$preset($size)\""] $content]
set fd [open $component w]
puts -nonewline $fd $content
close $fd
puts "Pinned core_vectorblox to $version with PRESET:$preset($size) ($size requested; mapping unverified)"
