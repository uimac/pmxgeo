import bpy
import bmesh
import os
import sys
import math
import mathutils
import os.path
import shutil

def copy_image(dst_folder, pmx, mat, texture_dict, image):
    src = image.filepath
    if os.path.exists(src):
        filename = os.path.basename(src)
        dst = dst_folder + filename
        if not os.path.exists(dst):
            shutil.copyfile(src, dst)
        
        if not filename in texture_dict:
            index = len(pmx.textures)
            texture_dict[filename] = index
            mat.diffuse_texture_index = index
            pmx.textures.append(filename)
        else:
            mat.diffuse_texture_index = texture_dict[filename]
            
def export_mesh(dst_folder, bm, pmx, vmd, frame, is_write_buffer, mesh_object, last_vertex_count, bmverts_count, vi_to_vis):
    import mmformat
    
    SWAP_YZ_MATRIX = mathutils.Matrix.Rotation(math.radians(90.0), 4, 'X')
    SWAP_YZ_MATRIX_INV = SWAP_YZ_MATRIX.inverted()
    
    if is_write_buffer:
        texture_dict = {}
        
        for v in bm.verts:
            co = SWAP_YZ_MATRIX_INV * mesh_object.matrix_world * v.co
            no = SWAP_YZ_MATRIX_INV * mesh_object.matrix_world * v.normal.normalized()
            co.z = -co.z
            no.z = -no.z
            vert = mmformat.PmxVertex()
            bdef = mmformat.PmxVertexSkinningBDEF1()
            for i in range(3):
                vert.position[i] = co[i]
                vert.normal[i] = no[i]

            vert.skinning = bdef.to_skinning()
            vert.skinning_type = mmformat.PmxVertexSkinningType.BDEF1
            pmx.vertices.append(vert)
        
        uv_layer = bm.loops.layers.uv.active
        uv_tex = bm.faces.layers.tex.active
            
        mat_to_face = {}
        for i, face in enumerate(bm.faces):
            if not(face.material_index in mat_to_face):
                mat_to_face[face.material_index] = []
            mat_to_face[face.material_index].append(face)
            
        additional_vertex_count = 0
        vi_to_uvs = {}
        for mat_index in mat_to_face:
            face_list = mat_to_face[mat_index]
            for face in face_list:
                vis = [face.loops[0].vert.index + last_vertex_count,\
                      face.loops[1].vert.index + last_vertex_count,\
                      face.loops[2].vert.index + last_vertex_count]
                if uv_layer:
                    for k, vi in enumerate(vis):
                        uv = (face.loops[k][uv_layer].uv[0], face.loops[k][uv_layer].uv[1])
                        if not (vi in vi_to_uvs):
                            vi_to_uvs[vi] = {}
                            vi_to_uvs[vi][uv] = vi
                        uv_to_vi = vi_to_uvs[vi]
                        if not (uv in uv_to_vi):
                            copy_v = pmx.vertices[vi]
                            additional_vi = last_vertex_count + len(bm.verts) + additional_vertex_count
                            vi_to_uvs[vi][uv] = additional_vi
                            vis[k] = additional_vi
                            
                            if not (vi in vi_to_vis):
                                vi_to_vis[vi] = [additional_vi]
                            else:
                                vi_to_vis[vi].append(additional_vi)
                            pmx.vertices.append(copy_v)
                            pmx.vertices[additional_vi].uv[0] = uv[0]
                            pmx.vertices[additional_vi].uv[1] = 1.0 - uv[1]
                            additional_vertex_count = additional_vertex_count + 1
                        else:
                            additional_vi = uv_to_vi[uv]
                            vis[k] = additional_vi
                            pmx.vertices[additional_vi].uv[0] = uv[0]
                            pmx.vertices[additional_vi].uv[1] = 1.0 - uv[1]
                        
                pmx.indices.append(vis[0])
                pmx.indices.append(vis[2])
                pmx.indices.append(vis[1])
                    
            if len(mesh_object.material_slots) > mat_index:
                bmat = mesh_object.material_slots[mat_index].material
                mat = mmformat.PmxMaterial()
                mat.material_name = "mat_" + str(mat_index)
                mat.diffuse[0] = bmat.diffuse_color[0]
                mat.diffuse[1] = bmat.diffuse_color[1]
                mat.diffuse[2] = bmat.diffuse_color[2]
                mat.diffuse[3] = 1
                mat.specular[0] = 0.0
                mat.specular[1] = 0.0
                mat.specular[2] = 0.0
                mat.ambient[0] = 0
                mat.ambient[1] = 0
                mat.ambient[2] = 0
                mat.diffuse_texture_index = -1
                mat.sphere_texture_index = -1
                mat.toon_texture_index = -1
                mat.index_count = len(face_list) * 3
                if bmat.use_nodes:
                    for node in bmat.node_tree.nodes:
                        #if node.type == 'BSDF_DIFFUSE':
                        if node.type == 'TEX_IMAGE':
                            copy_image(dst_folder, pmx, mat, texture_dict, node.image)
                elif uv_tex:
                    for i, slot in enumerate(bmat.texture_slots):
                        if slot and bmat.use_textures[i] and slot.use:
                            if slot.texture.type == 'IMAGE':
                                image = slot.texture.image
                                if image.source == 'FILE':
                                    copy_image(dst_folder, pmx, mat, texture_dict, image)
                pmx.materials.append(mat)
        
        pmx.bone_count = 1
        bone = mmformat.PmxBone()
        bone.as_center_bone()
        pmx.bones.append(bone)
        
        pmx.vertex_count = len(pmx.vertices)
        pmx.index_count = len(pmx.indices)
        pmx.material_count = len(pmx.materials)
        pmx.bone_count = len(pmx.bones)
        pmx.texture_count = len(pmx.textures)
    else:
        if not(len(bm.verts) == bmverts_count):
            ikframe = mmformat.VmdIkFrame()
            ikframe.frame = frame
            ikframe.display = False
            vmd.ik_frames.append(ikframe)
            return False

    morph = mmformat.PmxMorph()
    morph.morph_type = mmformat.MorphType.Vertex
    morph.category = mmformat.MorphCategory.Other
    morph.offset_count = len(bm.verts)
    morph.morph_name = "frame_" + str(frame)
    for i, v in enumerate(bm.verts):
        orgv = pmx.vertices[i].position
        co = SWAP_YZ_MATRIX_INV * mesh_object.matrix_world * v.co
        no = SWAP_YZ_MATRIX_INV * mesh_object.matrix_world * v.normal.normalized()
        co.z = -co.z
        no.z = -no.z
        sub = [ co[0]-orgv[0], co[1]-orgv[1], co[2]-orgv[2] ]
        offset = mmformat.PmxMorphVertexOffset()
        offset.position_offset[0] = sub[0]
        offset.position_offset[1] = sub[1]
        offset.position_offset[2] = sub[2]
        offset.vertex_index = i + last_vertex_count
        morph.vertex_offsets.append(offset)
        
        if offset.vertex_index in vi_to_vis:
            for vi in vi_to_vis[offset.vertex_index]:
                offset.vertex_index = vi
                morph.vertex_offsets.append(offset)
                
    pmx.morphs.append(morph)
    pmx.morph_count = pmx.morph_count + 1
    
    if not is_write_buffer:
        vmdframe = mmformat.VmdFaceFrame()
        vmdframe.face_name = morph.morph_name
        vmdframe.frame = frame - 1
        vmdframe.weight = 0.0
        vmd.face_frames.append(vmdframe)
        
    vmdframe = mmformat.VmdFaceFrame()
    vmdframe.face_name = morph.morph_name
    vmdframe.frame = frame
    vmdframe.weight = 1.0
    vmd.face_frames.append(vmdframe)
    
    vmdframe = mmformat.VmdFaceFrame()
    vmdframe.face_name = morph.morph_name
    vmdframe.frame = frame + 1
    vmdframe.weight = 0.0
    vmd.face_frames.append(vmdframe)
    
    if is_write_buffer:
        ikframe = mmformat.VmdIkFrame()
        ikframe.frame = frame
        ikframe.display = True
        vmd.ik_frames.append(ikframe)
    
    #print(pmx.vertex_count)
    #print(pmx.index_count)
    return True

def init_pmx(pmx):
    pmx.init()
    pmx.setting.bone_index_size = 1
    pmx.setting.material_index_size = 4
    pmx.setting.morph_index_size = 4
    pmx.setting.rigidbody_index_size = 4
    pmx.setting.texture_index_size = 4
    pmx.setting.vertex_index_size = 4
    pmx.setting.uv = 0
    pmx.setting.encoding = 0

def export_frames(dst_folder, context, mesh_objects, pmx, vmd, start_frame, frame_count):
    vi_to_vis = {}
    bmverts_count = {}
    last_vertex_counts = {}
    for frame in range(frame_count):
        current_frame = start_frame + frame
        context.scene.frame_set(current_frame)
        print("frame:", current_frame)
        is_write_buffer = (current_frame == start_frame)
    
        bpy.ops.object.duplicates_make_real()
        dupli_objects = [ob for ob in bpy.data.objects if ob.type == 'MESH' and ob.select and not (ob in mesh_objects)]
        if len(dupli_objects) > 0:
            for mesh_object in mesh_objects:
                mesh_object.select = False
                
            context.scene.objects.active = dupli_objects[0]
            bpy.ops.object.make_single_user(obdata=True)
            bpy.ops.object.join()
            dupli_object = context.scene.objects.active
            
            bm = bmesh.new()
            bm.from_object(dupli_object, context.scene)
            bmesh.ops.triangulate(bm, faces=bm.faces)
            if is_write_buffer:
                last_vertex_counts[dupli_object] = len(pmx.vertices)
                export_mesh(dst_folder, bm, pmx, vmd, current_frame, is_write_buffer, dupli_object, last_vertex_counts[dupli_object], 0, vi_to_vis)
                bmverts_count[dupli_object] = len(bm.verts)
                
                bpy.ops.object.delete()
                for mesh in mesh_objects:
                    mesh.select = True
                bm.free()
                del bm
            else:
                bpy.ops.object.delete()
                for mesh in mesh_objects:
                    mesh.select = True
                bm.free()
                del bm
                yield current_frame
        else:
            for mesh_object in mesh_objects:
                bm = bmesh.new()
                bm.from_object(mesh_object, context.scene)
                bmesh.ops.triangulate(bm, faces=bm.faces)
                if len(bm.verts) <= 0:
                    continue
                if is_write_buffer:
                    last_vertex_counts[mesh_object] = len(pmx.vertices)
                    export_mesh(dst_folder, bm, pmx, vmd, current_frame, is_write_buffer, mesh_object, last_vertex_counts[mesh_object], 0, vi_to_vis)
                    bmverts_count[mesh_object] = len(bm.verts)
                else:
                    res = export_mesh(dst_folder, bm, pmx, vmd, current_frame, is_write_buffer, mesh_object, last_vertex_counts[mesh_object], bmverts_count[mesh_object], vi_to_vis)
                    if not(res):
                        bm.free()
                        del bm
                        yield current_frame
                bm.free()
                del bm
                
    frame = start_frame + frame_count
    yield frame

def export_pmx(context):   
    import mmformat
    mesh_objects = [ob for ob in bpy.data.objects if ob.type == 'MESH' and ob.select] 
    model_base_name = 'out'
    dst_folder = 'D://pmx/'
    
    if len(mesh_objects) > 0:
        pmx = mmformat.PmxModel()
        vmd = mmformat.VmdMotion()
        init_pmx(pmx)
        
        start_frame = 0
        frame_count = 50
        
        gen = export_frames(dst_folder, context, mesh_objects, pmx, vmd, start_frame, frame_count)
        try:
            while True:
                frame = next(gen)
                # export pmx
                model_name = model_base_name + '_' + str(frame)
                pmx.model_name = model_name
                pmx.save_to_file(dst_folder + model_name + '.pmx')
                vmd.model_name = model_name
                print(len(vmd.ik_frames))
                vmd.save_to_file(dst_folder + model_name + '.vmd')
                # re create
                pmx = mmformat.PmxModel()
                vmd = mmformat.VmdMotion()
                init_pmx(pmx)
                # re generate
                frame_count = start_frame + frame_count - frame
                start_frame_org = start_frame
                start_frame = frame
                if frame_count > 0:
                    gen = export_frames(dst_folder, context, mesh_objects, pmx, vmd, start_frame, frame_count)
                    ikframe = mmformat.VmdIkFrame()
                    ikframe.frame = start_frame_org
                    ikframe.display = False
                    vmd.ik_frames.append(ikframe)
                    
        except Exception as e:
            print(e)
            pass

export_pmx(bpy.context)
