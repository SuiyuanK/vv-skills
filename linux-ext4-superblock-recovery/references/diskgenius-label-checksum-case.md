# DiskGenius EXT4 label/checksum recovery case

## Outcome

On 2026-08-05, an EXT4 Linux root filesystem became unbootable after its volume label was changed with DiskGenius Pro 5.4.6.1441. A narrow `debugfs` rewrite regenerated valid superblock checksums, after which the installed Linux system booted normally.

The evidence strongly supports this cause: DiskGenius changed the label field to `主分区` across readable EXT4 superblocks while leaving their CRC32C values inconsistent. Rufus boot-media creation and merely entering/exiting the installer were temporal coincidences; no installer write was established.

## Stable identity observed

- Physical disk: WD PC SN740 1 TB NVMe.
- Partition size: `895071813632` bytes, approximately 833.6 GiB / 895 GB decimal.
- Filesystem UUID: `98f1efd2-f2ba-4082-b3ba-795406799311`.
- GPT PARTUUID: `8c49ec3b-076f-48fb-8996-098c70a9d3d5`.
- Partition offset: sector `252221440` with 512-byte sectors.
- EXT4 block size: `4096` bytes.
- Relevant features: `64bit`, `metadata_csum_seed`, `sparse_super`, and `metadata_csum`.

The live environment exposed the target as `/dev/nvme0n1p3`, while the installed system later identified it as `/dev/nvme1n1p3`. Treat this as the central safety lesson: NVMe device numbers are session-dependent. The matching UUID, capacity, offset, and model identified the physical filesystem; the `/dev/nvme*` name did not.

## Failure evidence

Boot reached dracut/initramfs but repeatedly waited for:

```text
/dev/disk/by-uuid/98f1efd2-f2ba-4082-b3ba-795406799311
```

GNOME Disks saw the partition and GPT type `Linux Filesystem` but displayed `Contents: Unknown`.

Read-only probing found an EXT4 signature at offset `0x438`, the expected UUID, and the new label `主分区`. `dumpe2fs` decoded coherent filesystem geometry, state `clean`, root mount history, journal information, and matching UUID, then failed with:

```text
Superblock checksum does not match superblock
```

`e2fsck -f -n` likewise refused to open the filesystem because the superblock checksum was invalid. Backup blocks `32768` and `98304` did not provide usable EXT4 superblocks and triggered a message about an NTFS filesystem labelled `系统`; this was treated as an ambiguous or stale signature, not authorization to run NTFS repair. Backup block `1605632` contained coherent EXT4 metadata with the same new label and UUID, but its checksum also failed.

## Read-only commands used

```bash
sudo findmnt /dev/DEVICE
sudo blkid -p /dev/DEVICE
sudo wipefs -n /dev/DEVICE
sudo dumpe2fs -h /dev/DEVICE
sudo e2fsck -f -n -C 0 /dev/DEVICE
sudo mke2fs -n -t ext4 -b 4096 /dev/DEVICE
sudo dumpe2fs -h -o superblock=1605632 -o blocksize=4096 /dev/DEVICE
sudo e2fsck -f -n -b 1605632 -B 4096 -C 0 /dev/DEVICE
```

`mke2fs -n` was used only to print hypothetical backup-superblock locations. Omitting `-n` would create a new filesystem and destroy recovery prospects.

## Successful narrow repair

After confirming coherent EXT4 structures, the successful command in the live environment was:

```bash
sudo debugfs -n -w \
  -z /tmp/nvme0n1p3-superblock-fix.e2undo \
  -R 'set_super_value volume_name linuxroot' \
  /dev/nvme0n1p3
```

It was followed by:

```bash
sudo sync
sudo dumpe2fs -h /dev/nvme0n1p3
sudo e2fsck -f -n -C 0 /dev/nvme0n1p3
```

Linux subsequently booted normally.

For future use, improve this command by putting the `.e2undo` file on another persistent filesystem and substituting a freshly rediscovered device path. In `debugfs`, `-n` disables metadata checksum verification, `-w` enables writes, and `-z` records overwritten blocks. The undo file cannot recover a sudden power or system failure.

## Post-repair verification

A later live-system check exposed the same UUID as `/dev/nvme2n1p3`, further confirming that the NVMe device number is not stable. The filesystem label had subsequently been changed to `ROOT`.

`e2fsck -f -n -C 0` completed passes 1 through 5 and returned exit status `0`. It printed optional optimization suggestions for inodes `26613902`, `26619767`, and `38831709`:

```text
extent tree (at level 1) could be narrower. Optimize? no
```

These messages mean that the extent index could be compacted; they are not filesystem errors. Declining the optimization is valid when the complete check returns `0`. The final summary was:

```text
ROOT: 1058876/54632448 files (0.5% non-contiguous), 56564052/218523392 blocks
```

`dumpe2fs -h` independently reported `Filesystem state: clean`, the original filesystem UUID, label `ROOT`, and a valid CRC32C superblock checksum (`0xf7b37912`). Together, the completed passes, exit status `0`, and clean superblock state are decisive evidence that the filesystem is healthy even if DiskGenius continues to display `损坏`.

## Do not generalize blindly

This repair is appropriate only when multiple superblocks contain coherent matching metadata and the defect is isolated to stale superblock checksums after an external label change. It is not a general repair for I/O errors, missing partitions, wrong offsets, widespread inode/block checksum failures, overwritten filesystems, or a genuinely active NTFS filesystem.
