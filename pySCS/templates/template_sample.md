
# Security Control Selection Sample
***

## System Description

{scs.description}

## Dataflow Diagram

![Level 0 DFD](dfd.png)

## Sequence Diagram

![Level 0 SEQ](seq.png)

## Dataflows

Name|From|To |Data|Protocol|Port
----|----|---|----|--------|----
{dataflows:repeat:{{item.name}}|{{item.source.name}}|{{item.sink.name}}|{{item.data}}|{{item.protocol}}|{{item.dstPort}}
}

## Control list

{findings:repeat:* {{item.description}} on element "{{item.target}}"
}
