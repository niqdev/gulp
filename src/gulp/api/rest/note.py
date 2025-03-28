"""
This module contains the REST API for gULP (gui Universal Log Processor).
"""

from typing import Annotated

import muty.crypto
import muty.file
import muty.jsend
import muty.list
import muty.log
import muty.os
import muty.string
import muty.uploadfile
from fastapi import APIRouter, Body, Header, Query
from fastapi.responses import JSONResponse
from muty.jsend import JSendException, JSendResponse
from gulp.utils import logger
import gulp.api.collab_api as collab_api
import gulp.api.rest.collab_utility as collab_utility
import gulp.defs
import gulp.plugin
import gulp.utils
from gulp.api.collab.base import (
    GulpAssociatedEvent,
    GulpCollabFilter,
    GulpCollabLevel,
    GulpCollabType,
)
from gulp.api.collab.collabobj import CollabObj
from gulp.defs import InvalidArgument

_app: APIRouter = APIRouter()


@_app.post(
    "/note_list",
    tags=["note"],
    response_model=JSendResponse,
    response_model_exclude_none=True,
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "timestamp_msec": 1701278479259,
                        "req_id": "903546ff-c01e-4875-a585-d7fa34a0d237",
                        "data": [
                            "CollabObj",
                        ],
                    }
                }
            }
        }
    },
    summary="list notes, optionally using a filter.",
    description="available filters: id, owner_id, operation_id, context, src_file, name(=title), text, time_start(=pin time), time_end, events, tags, private_only, level, limit, offset.",
)
async def note_list_handler(
    token: Annotated[str, Header(description=gulp.defs.API_DESC_TOKEN)],
    flt: Annotated[GulpCollabFilter, Body()] = None,
    req_id: Annotated[str, Query(description=gulp.defs.API_DESC_REQID)] = None,
) -> JSendResponse:
    req_id = gulp.utils.ensure_req_id(req_id)
    return await collab_utility.collabobj_list(token, req_id, GulpCollabType.NOTE, flt)


@_app.get(
    "/note_get_by_id",
    tags=["note"],
    response_model=JSendResponse,
    response_model_exclude_none=True,
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "timestamp_msec": 1701278479259,
                        "req_id": "903546ff-c01e-4875-a585-d7fa34a0d237",
                        "data": {"CollabObj"},
                    }
                }
            }
        }
    },
    summary="gets a note.",
)
async def note_get_by_id_handler(
    token: Annotated[str, Header(description=gulp.defs.API_DESC_TOKEN)],
    note_id: Annotated[int, Query(description="id of the note to be retrieved.")],
    req_id: Annotated[str, Query(description=gulp.defs.API_DESC_REQID)] = None,
) -> JSendResponse:
    req_id = gulp.utils.ensure_req_id(req_id)
    return await collab_utility.collabobj_get_by_id(
        token, req_id, GulpCollabType.NOTE, note_id
    )


@_app.delete(
    "/note_delete",
    tags=["note"],
    response_model=JSendResponse,
    response_model_exclude_none=True,
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "timestamp_msec": 1701278479259,
                        "req_id": "903546ff-c01e-4875-a585-d7fa34a0d237",
                        "data": {"id": 1},
                    }
                }
            }
        }
    },
    summary="deletes a note.",
)
async def note_delete_handler(
    token: Annotated[str, Header(description=gulp.defs.API_DESC_DELETE_EDIT_TOKEN)],
    note_id: Annotated[int, Query(description="id of the note to be deleted.")],
    ws_id: Annotated[str, Query(description=gulp.defs.API_DESC_WS_ID)],
    req_id: Annotated[str, Query(description=gulp.defs.API_DESC_REQID)] = None,
) -> JSendResponse:
    req_id = gulp.utils.ensure_req_id(req_id)
    return await collab_utility.collabobj_delete(
        token, req_id, GulpCollabType.NOTE, note_id, ws_id=ws_id
    )


@_app.put(
    "/note_update",
    tags=["note"],
    response_model=JSendResponse,
    response_model_exclude_none=True,
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "timestamp_msec": 1701278479259,
                        "req_id": "903546ff-c01e-4875-a585-d7fa34a0d237",
                        "data": {"CollabObj"},
                    }
                }
            }
        }
    },
    summary="updates an existing note.",
)
async def note_update_handler(
    token: Annotated[str, Header(description=gulp.defs.API_DESC_EDIT_TOKEN)],
    note_id: Annotated[int, Query(description="id of the note to be updated.")],
    ws_id: Annotated[str, Query(description=gulp.defs.API_DESC_WS_ID)],
    events: Annotated[list[GulpAssociatedEvent], Body()] = None,
    text: Annotated[str, Body()] = None,
    title: Annotated[str, Body()] = None,
    tags: Annotated[
        list[str], Body()
    ] = None,
    glyph_id: Annotated[
        int, Query(description="optional new glyph ID for the note.")
    ] = None,
    color: Annotated[
        str, Query(description="optional new note color in #rrggbb or css-name format.")
    ] = None,
    private: Annotated[bool, Query(description="whether the note is private.")] = None,
    req_id: Annotated[str, Query(description=gulp.defs.API_DESC_REQID)] = None,
) -> JSendResponse:
    req_id = gulp.utils.ensure_req_id(req_id)
    try:
        if (
            events is None
            and text is None
            and title is None
            and tags is None
            and glyph_id is None
            and color is None
            and private is None
        ):
            raise InvalidArgument(
                "at least one of event_ids, text, title, glyph_id, tags, color, private must be set."
            )

        o = await CollabObj.update(
            await collab_api.collab(),
            token,
            req_id,
            note_id,
            ws_id,
            name=title,
            txt=text,
            events=events,
            glyph_id=glyph_id,
            tags=tags,
            data={"color": color} if color is not None else None,
            t=GulpCollabType.NOTE,
            private=private,
        )
        return JSONResponse(muty.jsend.success_jsend(req_id=req_id, data=o.to_dict()))
    except Exception as ex:
        raise JSendException(req_id=req_id, ex=ex) from ex


@_app.post(
    "/note_create",
    tags=["note"],
    response_model=JSendResponse,
    response_model_exclude_none=True,
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "timestamp_msec": 1701278479259,
                        "req_id": "903546ff-c01e-4875-a585-d7fa34a0d237",
                        "data": {"CollabObj"},
                    }
                }
            }
        }
    },
    summary='creates a note, associated with events ( { "id": ..., "@timestamp": ..."} ) or pinned at a certain time.',
)
async def note_create_handler(
    token: Annotated[str, Header(description=gulp.defs.API_DESC_EDIT_TOKEN)],
    operation_id: Annotated[
        int, Query(description="operation to be associated with this note.")
    ],
    context: Annotated[
        str, Query(description="context to be associated with this note.")
    ],
    src_file: Annotated[
        str, Query(description="source file to be associated with this note.")
    ],
    ws_id: Annotated[str, Query(description=gulp.defs.API_DESC_WS_ID)],
    text: Annotated[str, Body()],
    title: Annotated[str, Body()],
    time_pin: Annotated[
        int,
        Query(description="timestamp to pin the note to."),
    ] = None,
    events: Annotated[list[GulpAssociatedEvent], Body()] = None,
    tags: Annotated[
        list[str],
        Body(),
    ] = None,
    glyph_id: Annotated[int, Query(description="glyph ID for the new note.")] = None,
    color: Annotated[
        str,
        Query(
            description='optional color in #rrggbb or css-name format, default is "green".'
        ),
    ] = "green",
    private: Annotated[bool, Query(description=gulp.defs.API_DESC_PRIVATE)] = False,
    level: Annotated[
        GulpCollabLevel, Query(description=gulp.defs.API_DESC_COLLAB_LEVEL)
    ] = GulpCollabLevel.DEFAULT,
    req_id: Annotated[str, Query(description=gulp.defs.API_DESC_REQID)] = None,
) -> JSendResponse:
    req_id = gulp.utils.ensure_req_id(req_id)

    try:
        if events is None and time_pin is None:
            raise InvalidArgument("events and time_pin cannot be both None.")
        if events is not None and time_pin is not None:
            raise InvalidArgument("events and time_pin cannot be both set.")

        # logger().debug('events=%s' % (events))
        o = await CollabObj.create(
            await collab_api.collab(),
            token,
            req_id,
            GulpCollabType.NOTE,
            ws_id=ws_id,
            operation_id=operation_id,
            name=title,
            context=context,
            src_file=src_file,
            txt=text,
            time_start=time_pin,
            events=events,
            glyph_id=glyph_id,
            tags=tags,
            data={"color": color},
            private=private,
            level=level,
        )
        return JSONResponse(muty.jsend.success_jsend(req_id=req_id, data=o.to_dict()))
    except Exception as ex:
        raise JSendException(req_id=req_id, ex=ex) from ex


def router() -> APIRouter:
    """
    Returns this module api-router, to add it to the main router

    Returns:
        APIRouter: The APIRouter instance
    """
    global _app
    return _app
