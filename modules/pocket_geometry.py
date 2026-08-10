from pathlib import Path


class PocketGeometry:

    def calculate(self, pocket_file):

        xs = []
        ys = []
        zs = []

        with open(pocket_file) as f:

            for line in f:

                if not line.startswith("ATOM"):
                    continue

                fields = line.split()

                xs.append(float(fields[5]))
                ys.append(float(fields[6]))
                zs.append(float(fields[7]))

        if not xs:
            raise ValueError("Pocket contains no alpha spheres.")

        center = (
            sum(xs) / len(xs),
            sum(ys) / len(ys),
            sum(zs) / len(zs)
        )

        size = (
            max(xs) - min(xs) + 6.0,
            max(ys) - min(ys) + 6.0,
            max(zs) - min(zs) + 6.0
        )

        return {

            "center_x": center[0],
            "center_y": center[1],
            "center_z": center[2],

            "size_x": size[0],
            "size_y": size[1],
            "size_z": size[2]

        }
