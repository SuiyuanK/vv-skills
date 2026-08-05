---
name: linux-ext4-superblock-recovery
description: Safely diagnose and recover an unbootable Linux EXT4 filesystem, especially after an abnormal shutdown or a Windows partition tool such as DiskGenius changes an EXT4 label and leaves invalid metadata checksums. Use for dracut UUID timeouts, GNOME Disks showing Contents Unknown, e2fsck superblock checksum failures, ambiguous EXT4/NTFS signatures, backup-superblock testing, or confirmation-gated debugfs checksum repair.
---

# Linux EXT4 Superblock Recovery

## Purpose

Diagnose an inaccessible EXT4 root partition without turning a recoverable metadata problem into data loss. Begin read-only, identify the physical partition by stable evidence, and permit writes only after the failure mode and rollback path are clear.

## Non-negotiable safety rules

- Never reuse `/dev/nvmeXnYpZ` from another boot or operating system without rediscovery. NVMe numbering can change between a live environment and the installed system.
- Identify the target using several independent fields: model, capacity, partition size and offset, filesystem UUID, and GPT PARTUUID. A device node alone is not identity.
- Keep the target unmounted for `e2fsck`. If `findmnt` returns a mount, stop and unmount it from the live environment.
- Do not run `mkfs`, `mke2fs` without `-n`, `e2fsck -y`, `ntfsfix`, `chkdsk`, format, delete, or partition-table repair during diagnosis.
- Treat a surprise NTFS signature as ambiguity or stale metadata until raw signatures and partition history are reconciled. Do not switch to NTFS repair merely because `e2fsck` prints `contains a ntfs file system`.
- Prefer a full clone when data is irreplaceable. Put every undo file on another filesystem; `/tmp` is only a short-lived fallback and disappears after reboot.
- Before a write, state the exact device, evidence identifying it, blocks or fields to be changed, backup location, and verification plan.

## Workflow

### 1. Establish the symptom

Extract the requested UUID from the boot log or kernel command line. A repeated dracut wait for `/dev/disk/by-uuid/<uuid>` means the bootloader and kernel started but initramfs could not resolve the root filesystem.

Do not attribute the failure to boot-media creation merely because it happened nearby in time. Check for partition-tool writes, BIOS storage-mode changes, filesystem errors, and device enumeration changes.

### 2. Rediscover the target read-only

Run from a Linux live system:

```bash
lsblk -o NAME,SIZE,TYPE,FSTYPE,UUID,PARTUUID,PARTTYPE,PARTLABEL,LABEL,MOUNTPOINTS,MODEL
sudo blkid -p /dev/DEVICE
sudo fdisk -l
sudo findmnt /dev/DEVICE
```

Replace `/dev/DEVICE` only after matching the expected physical disk and partition. Preserve the output before proceeding.

### 3. Inspect signatures and EXT4 metadata

```bash
sudo wipefs -n --output DEVICE,OFFSET,TYPE,UUID,LABEL /dev/DEVICE
sudo dumpe2fs -h /dev/DEVICE
sudo e2fsck -f -n -C 0 /dev/DEVICE
```

Interpret the results:

- UUID and EXT4 metadata are readable and `e2fsck -n` completes: do not repair merely because a Windows tool says damaged.
- `Inode N extent tree (at level 1) could be narrower. Optimize? no` is an optional extent-tree compaction suggestion, not corruption. If passes 1 through 5 complete and the exit status is `0`, do not rerun a writable check merely to accept this optimization.
- `dumpe2fs` prints coherent EXT4 geometry and then reports `Superblock checksum does not match superblock`: suspect a changed superblock field with a stale checksum.
- `Bad magic number` with no coherent EXT4 evidence: verify the device and partition boundaries before trying backup superblocks.
- I/O errors, NVMe media errors, or disappearing devices: stop filesystem repair and prioritize imaging/hardware diagnosis.

### 4. Test backup superblocks without writing

Use `mke2fs` only with `-n` to calculate candidate locations:

```bash
sudo mke2fs -n -t ext4 -b 4096 /dev/DEVICE
```

Use the actual block size from `dumpe2fs`; do not assume 4096 for an unknown filesystem. Test a listed candidate:

```bash
sudo dumpe2fs -h -o superblock=BACKUP_BLOCK -o blocksize=BLOCK_SIZE /dev/DEVICE
sudo e2fsck -f -n -b BACKUP_BLOCK -B BLOCK_SIZE -C 0 /dev/DEVICE
```

If a backup is valid, keep the check read-only until important data is backed up. If several backups contain coherent identical metadata but all fail only the superblock checksum, read the DiskGenius label-change case before considering the narrow debugfs repair.

### 5. Validate data structures while ignoring only checksum verification

Without `-w`, `debugfs` remains read-only. Its `-n` option disables metadata checksum verification; it does not by itself enable writes.

```bash
sudo debugfs -n -R 'ls -l /' /dev/DEVICE
sudo debugfs -n -R 'ls -l /home' /dev/DEVICE
```

Require plausible root directories and expected user data. If directory traversal fails or metadata is inconsistent beyond the superblock checksum, stop and use a clone/data-recovery workflow.

### 6. Apply the narrow label/checksum repair only when evidence matches

Read `references/diskgenius-label-checksum-case.md`. Use this path only when all of the following hold:

1. The target is unmounted and identified by stable fields.
2. Main or backup superblocks show coherent, matching filesystem geometry and the expected UUID.
3. The same newly assigned label appears in those superblocks.
4. The decisive error is a superblock checksum mismatch, without I/O errors.
5. `debugfs -n` can traverse the expected directory tree.
6. A clone exists, or the user explicitly accepts the minimal-write path with an undo file.

Use a plain ASCII label to avoid reproducing the external tool's label encoding or checksum behavior:

```bash
sudo debugfs -n -w \
  -z /path/on-another-filesystem/ext4-superblock-fix.e2undo \
  -R 'set_super_value volume_name linuxroot' \
  /dev/DEVICE
```

This command is destructive in the technical sense because `-w` writes. Explain that `-n` here means ignore checksum verification, `-z` records overwritten blocks, and the undo file does not protect against a power failure. Keep the machine on reliable power.

### 7. Verify before normal boot

```bash
sudo sync
sudo dumpe2fs -h /dev/DEVICE
sudo e2fsck -f -n -C 0 /dev/DEVICE
echo $?
```

Require all of the following before declaring the repair successful:

- `dumpe2fs` no longer reports a superblock checksum mismatch.
- `e2fsck` opens the filesystem and completes its passes.
- `e2fsck` returns exit status `0`; optimization-only `could be narrower` messages do not invalidate this result.
- The filesystem UUID still matches the boot configuration.
- No I/O errors appear.

If the read-only check reports additional inconsistencies, back up data before an interactive `e2fsck`; do not jump to blanket `-y`. A cautious read-only mount for backup is:

```bash
sudo mkdir -p /mnt/linuxroot
sudo mount -o ro,noload /dev/DEVICE /mnt/linuxroot
```

After reboot, verify the actual root device again rather than expecting the live-system NVMe number:

```bash
findmnt /
lsblk -f
sudo dmesg -T | grep -Ei 'ext4|nvme|i/o error|corrupt|filesystem error'
```

## Reference

Read `references/diskgenius-label-checksum-case.md` for the verified 2026-08 recovery evidence, commands, false leads, and device-numbering lesson.
