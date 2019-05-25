
# Security Control Selection Sample
***

## System Description

{scs.description}

## Dataflow Diagram

![](dfd.png)

## Dataflows

Name|From|To |Data|Protocol|Port
----|----|---|----|--------|----
{dataflows:repeat:{{item.name}}|{{item.source.name}}|{{item.sink.name}}|{{item.data}}|{{item.protocol}}|{{item.dstPort}}
}

## Control list
Element|Issue
-----|-------
{findings:repeat:{{item.target}}|{{item.description}}
}

## Checked controls
ID|Description|Mitigation
--|-----------|----------
{controls:repeat:{{item.id}}|{{item.description}}|{{item.mitigation}}
}